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
    @staticmethod
    def parse_date(date_str: str) -> Tuple[datetime, datetime]:
        """
        Parse date expressions into start and end datetime objects.
        
        Args:
            date_str: Date expression like "yesterday", "last week", etc.
            
        Returns:
            Tuple of start and end datetime objects
        """
        date_str = date_str.lower().strip()
        now = datetime.now()

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
            try:
                date = parser.parse(date_str)
                return date, date
            except:
                raise ValueError(f"Could not parse date: {date_str}")


class EnhancedQueryEngine:
    def __init__(self, top_k: int = 3):
        """
        Initialize query engine with document indexer and OpenAI.
        
        Args:
            top_k: Number of top results to retrieve
        """
        self.document_indexer = DocumentIndexer()
        self.llm = OpenAI(model="gpt-4-turbo-preview")
        self.top_k = top_k
        self.date_parser = DateParser()

    def _extract_metadata_filters(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract metadata filters from natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of cleaned query and extracted metadata filters
        """
        metadata_filters = {}
        cleaned_query = query

        # Date pattern extraction
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

        # Other metadata extraction
        for field in FILTERING_METADATA:
            if field in ["created_time", "modified_time"]:
                continue
            pattern = rf"{field}:\s*([^\s]+)"
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                metadata_filters[field] = match.group(1)
                cleaned_query = cleaned_query.replace(match.group(0), "").strip()

        # Keyword mapping: natural terms to file_type filters
        keyword_map = {
            "images": "image",
            "pictures": "image",
            "photos": "image",
            "videos": "video",
            "clips": "video",
            "audio": "audio",
            "recordings": "audio",
            "documents": "document",
            "pdfs": "document",
            "spreadsheets": "document",
            "sheets": "document",
            "excel": "document",
            "csv": "document",
            "txt": "document",
            "markdown": "document",
            "ppt": "document",
            "powerpoint": "document",
            "slides": "document",
            "slideshow": "document",
            "slideshows": "document",
        }

        for word, file_type in keyword_map.items():
            if word in cleaned_query.lower():
                metadata_filters["file_type"] = file_type
                cleaned_query = re.sub(
                    word, "", cleaned_query, flags=re.IGNORECASE
                ).strip()

        return cleaned_query, metadata_filters

    def _apply_metadata_filters(self, nodes, filters: Dict[str, Any]):
        """Apply metadata filters to retrieved nodes"""
        if not filters:
            return nodes
        
        filtered_nodes = []
        for node in nodes:
            if self._matches_filters(node, filters):
                filtered_nodes.append(node)
        
        return filtered_nodes

    def hybrid_query(
        self,
        query_text: str,
        folder_id: str,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and metadata filtering.
        
        Args:
            query_text: User query text
            folder_id: ID of the folder to search
            metadata_filters: Optional additional metadata filters
            
        Returns:
            List of matching nodes
        """
        # Extract metadata filters from query
        cleaned_query, extracted_filters = self._extract_metadata_filters(query_text)

        if metadata_filters:
            extracted_filters.update(metadata_filters)

        # Get the index for the folder
        index = self.document_indexer.get_index(folder_id)
        if not index:
            return []

        # If query is empty, do metadata-only search
        if not cleaned_query.strip():
            return self._metadata_only_search(index, extracted_filters)

        # Setup retriever with similarity parameters
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=self.top_k,
            similarity_cutoff=0.7,
        )
        
        # Retrieve nodes based on semantic similarity
        nodes = retriever.retrieve(cleaned_query)

        # Apply additional metadata filters if any
        if extracted_filters:
            nodes = self._apply_metadata_filters(nodes, extracted_filters)

        return nodes

    def _metadata_only_search(self, index, metadata_filters: Dict[str, Any]):
        """Search based only on metadata without semantic query"""
        matching_nodes = []
        for node in index.docstore.docs.values():
            if self._matches_filters(node, metadata_filters):
                matching_nodes.append(node)
        return matching_nodes

    def _matches_filters(self, node, filters: Dict[str, Any]) -> bool:
        """Check if a node matches all the specified filters"""
        for key, value in filters.items():
            if key == "date":
                node_date = node.metadata.get("created_time") or node.metadata.get(
                    "modified_time"
                )
                if not node_date or not self._date_matches(node_date, value):
                    return False
            elif key in FILTERING_METADATA:
                if not self._value_matches(node.metadata.get(key), value):
                    return False
        return True

    def _date_matches(self, node_date: str, target_date: str) -> bool:
        """Check if a node's date matches the target date expression"""
        try:
            node_dt = datetime.fromisoformat(node_date.replace("Z", "+00:00"))
            start_dt, end_dt = DateParser.parse_date(target_date)
            return start_dt <= node_dt <= end_dt
        except Exception as e:
            print(f"Error in date matching: {str(e)}")
            return False

    def _value_matches(self, node_value: Any, target_value: Any) -> bool:
        """Check if a node's value matches the target value with operators"""
        if node_value is None:
            return False

        if isinstance(target_value, str):
            match = re.match(r"([<>]=?|~=|=)?(.+)", target_value)
            if not match:
                return str(node_value).lower() == target_value.lower()
            operator, val = match.groups()
            val = val.strip()

            if operator in ["~", "~="]:
                return val.lower() in str(node_value).lower()
            elif operator == ">":
                try:
                    return float(node_value) > float(val)
                except:
                    return False
            elif operator == "<":
                try:
                    return float(node_value) < float(val)
                except:
                    return False
            elif operator == ">=":
                try:
                    return float(node_value) >= float(val)
                except:
                    return False
            elif operator == "<=":
                try:
                    return float(node_value) <= float(val)
                except:
                    return False
            elif operator == "=":
                return str(node_value).lower() == val.lower()
            else:
                return str(node_value).lower() == target_value.lower()

        if isinstance(target_value, list):
            return any(str(node_value).lower() == str(v).lower() for v in target_value)

        return node_value == target_value

    def query(
        self, query_text: str, folder_id: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Perform a complete query including metadata extraction and answer generation.
        
        Args:
            query_text: User query text
            folder_id: ID of the folder to search
            
        Returns:
            Tuple of answer text and source information
        """
        query_text, metadata_filters = self._extract_metadata_filters(query_text)
        results = self.hybrid_query(query_text, folder_id, metadata_filters)

        if not results:
            return (
                "I couldn't find any relevant documents in your folder to answer this question. Please make sure the documents you're looking for are in the selected folder and try again.",
                [],
            )

        # Create context from retrieved nodes
        context = "\n\n".join([f"Document: {node.text}" for node in results])
        
        # Generate prompt for the LLM
        prompt = f"""Based on the following documents, please provide a comprehensive answer to the question: {query_text}

Documents:
{context}

Please provide a very concise answer that synthesizes information from the relevant documents. If the documents don't contain enough information to answer the question, please say so."""

        # Get answer from LLM
        answer = self.llm.complete(prompt).text

        # Format sources for return
        sources = [
            {
                "text": node.text,
                "metadata": node.metadata,
                "score": getattr(node, "score", None),
                "file_name": node.metadata.get("file_name", "Unknown"),
                "mime_type": node.metadata.get("mime_type", "Unknown"),
                "web_view_link": node.metadata.get("web_view_link", "Unknown"),
            }
            for node in results
        ]

        return answer, sources
