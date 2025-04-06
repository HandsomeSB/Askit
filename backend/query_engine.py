# query_engine.py
from typing import List, Dict, Any, Tuple, Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta

# Load environment variables from .env file
load_dotenv()

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.llms.openai import OpenAI
from llama_index.core.postprocessor import SimilarityPostprocessor

from indexer import DocumentIndexer, FILTERING_METADATA

METADATA_FIELDS = {
    "date": ["created_time", "modified_time"],
    "location": ["latitude", "longitude"],
    "camera": ["camera_make", "camera_model"],
}


class DateParser:
    """Utility class to parse various date formats and relative dates"""

    @staticmethod
    def parse_date(date_str: str) -> Tuple[datetime, datetime]:
        """
        Parse a date string into start and end datetime objects.
        Handles various formats:
        - "before/after July 10"
        - "between July and August 2025"
        - "yesterday"
        - "last week"
        - "last month"
        - "last year"
        - "this month"
        - "this year"
        """
        date_str = date_str.lower().strip()
        now = datetime.now()

        # Handle relative dates
        if date_str == "yesterday":
            start = now - timedelta(days=1)
            end = start + timedelta(days=1)
            return start, end
        elif date_str == "last week":
            start = now - timedelta(days=7)
            end = now
            return start, end
        elif date_str == "last month":
            start = now - relativedelta(months=1)
            end = now
            return start, end
        elif date_str == "last year":
            start = now - relativedelta(years=1)
            end = now
            return start, end
        elif date_str == "this month":
            start = now.replace(day=1)
            end = now
            return start, end
        elif date_str == "this year":
            start = now.replace(month=1, day=1)
            end = now
            return start, end

        # Handle before/after patterns
        before_match = re.match(r"before\s+(.+)", date_str)
        after_match = re.match(r"after\s+(.+)", date_str)
        between_match = re.match(r"between\s+(.+)\s+and\s+(.+)", date_str)

        if before_match:
            date = parser.parse(before_match.group(1))
            return datetime.min, date
        elif after_match:
            date = parser.parse(after_match.group(1))
            return date, datetime.max
        elif between_match:
            start_date = parser.parse(between_match.group(1))
            end_date = parser.parse(between_match.group(2))
            return start_date, end_date
        else:
            # Try to parse as a single date
            try:
                date = parser.parse(date_str)
                return date, date
            except:
                raise ValueError(f"Could not parse date: {date_str}")


class EnhancedQueryEngine:
    """
    Process user queries and generate answers based on document indices.
    Supports both semantic search and metadata filtering.
    """

    def __init__(self, top_k: int = 10):
        """
        Initialize query engine.

        Args:
            top_k: Number of top documents to retrieve
        """
        self.document_indexer = DocumentIndexer()
        self.llm = OpenAI(model="gpt-4-turbo-preview")
        self.top_k = top_k
        self.date_parser = DateParser()

    def _extract_metadata_filters(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract metadata filters from the query.

        Args:
            query: User query string

        Returns:
            Tuple of (cleaned_query, metadata_filters)
        """
        metadata_filters = {}
        cleaned_query = query

        # Extract date filters
        date_patterns = [
            (
                r"(before|after)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
                "date",
            ),
            (
                r"between\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)\s+and\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)",
                "date_range",
            ),
            (
                r"(yesterday|last week|last month|last year|this month|this year)",
                "relative_date",
            ),
        ]

        for pattern, filter_type in date_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if filter_type == "date":
                    metadata_filters["date"] = f"{match.group(1)} {match.group(2)}"
                elif filter_type == "date_range":
                    metadata_filters["date"] = (
                        f"between {match.group(1)} and {match.group(2)}"
                    )
                else:
                    metadata_filters["date"] = match.group(1)
                cleaned_query = cleaned_query.replace(match.group(0), "").strip()

        # Extract other metadata filters
        for field in FILTERING_METADATA:
            if field in ["created_time", "modified_time"]:
                continue  # Already handled by date filters

            pattern = rf"{field}:\s*([^\s]+)"
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                metadata_filters[field] = match.group(1)
                cleaned_query = cleaned_query.replace(match.group(0), "").strip()

        return cleaned_query, metadata_filters

    def hybrid_query(
        self,
        query_text: str,
        folder_id: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a query against a specific folder index.

        Args:
            query_text: User query text
            folder_id: Google Drive folder ID to query against
            metadata_filters: Optional additional metadata filters

        Returns:
            List of matching documents with scores
        """
        # Extract metadata filters from query
        cleaned_query, extracted_filters = self._extract_metadata_filters(query_text)

        # Combine extracted filters with provided filters
        if metadata_filters:
            extracted_filters.update(metadata_filters)

        # Get the index
        index = self.document_indexer.get_index(folder_id)
        if not index:
            return []

        # If no query text, only do metadata filtering
        if not cleaned_query.strip():
            return self._metadata_only_search(index, extracted_filters)

        # Get semantic search results
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=self.top_k,
            similarity_cutoff=0.5,  # Lower threshold to allow more matches
        )
        nodes = retriever.retrieve(cleaned_query)

        # Apply metadata filters if provided
        if extracted_filters:
            nodes = self._apply_metadata_filters(nodes, extracted_filters)

        return nodes

    def _metadata_only_search(self, index, metadata_filters: Dict[str, Any]):
        """
        Search based only on metadata filters
        """
        matching_nodes = []
        for node in index.docstore.docs.values():
            if self._matches_filters(node, metadata_filters):
                matching_nodes.append(node)
        return matching_nodes

    def _matches_filters(self, node, filters: Dict[str, Any]) -> bool:
        """
        Check if a node matches all provided filters
        """
        for key, value in filters.items():
            if key == "date":
                # Handle date filtering
                node_date = node.metadata.get("created_time") or node.metadata.get(
                    "modified_time"
                )
                if not node_date or not self._date_matches(node_date, value):
                    return False
            elif key in FILTERING_METADATA:
                # Handle other metadata filtering
                if not self._value_matches(node.metadata.get(key), value):
                    return False
        return True

    def _date_matches(self, node_date: str, target_date: str) -> bool:
        """
        Check if the node's date falls within the target date range
        """
        try:
            # Parse the node's date
            node_dt = datetime.fromisoformat(node_date.replace("Z", "+00:00"))

            # Parse the target date range
            start_dt, end_dt = DateParser.parse_date(target_date)

            # Check if node date falls within the range
            return start_dt <= node_dt <= end_dt
        except Exception as e:
            print(f"Error in date matching: {str(e)}")
            return False

    def _value_matches(self, node_value: Any, target_value: Any) -> bool:
        """
        Check if a metadata value matches the target value
        """
        if node_value is None:
            return False

        # Handle numeric comparisons
        if isinstance(target_value, (int, float)):
            try:
                node_num = float(node_value)
                return node_num == target_value
            except (ValueError, TypeError):
                return False

        # Handle string comparisons
        if isinstance(target_value, str):
            return str(node_value).lower() == target_value.lower()

        # Handle list comparisons
        if isinstance(target_value, list):
            return any(str(node_value).lower() == str(v).lower() for v in target_value)

        return False

    def query(
        self, query_text: str, folder_id: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query the system with a question, restricted to a specific folder.

        Args:
            query_text: The query text
            folder_id: The folder ID to search in

        Returns:
            Tuple of (answer, sources)
        """
        # Extract metadata filters from the query
        query_text, metadata_filters = self._extract_metadata_filters(query_text)

        # Perform the hybrid query
        results = self.hybrid_query(query_text, folder_id, metadata_filters)

        # Format the results into answer and sources
        if not results:
            return "No relevant documents found.", []

        # Generate a comprehensive answer using the LLM
        context = "\n\n".join([f"Document: {node.text}" for node in results])
        prompt = f"""Based on the following documents, please provide a comprehensive answer to the question: {query_text}

Documents:
{context}

Please provide a detailed answer that synthesizes information from the relevant documents."""

        answer = self.llm.complete(prompt).text

        # Format sources
        sources = [
            {"text": node.text, "metadata": node.metadata, "score": node.score}
            for node in results
        ]

        return answer, sources
