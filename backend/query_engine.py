# query_engine.py
from typing import List, Dict, Any, Tuple
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.llms.openai import OpenAI
from llama_index.core.postprocessor import SimilarityPostprocessor

from indexer import DocumentIndexer


class QueryEngine:
    """
    Process user queries and generate answers based on document indices.
    """

    def __init__(self, top_k: int = 5):
        """
        Initialize query engine.

        Args:
            top_k: Number of top documents to retrieve
        """
        self.document_indexer = DocumentIndexer()
        self.llm = OpenAI(model="gpt-4", temperature=0)
        self.top_k = top_k

    def query(
        self, query_text: str, folder_id: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a query against a specific folder index.

        Args:
            query_text: User query text
            folder_id: Google Drive folder ID to query against

        Returns:
            Tuple of (answer_text, source_documents)
        """
        try:
            # Get the index for the folder
            index = self.document_indexer.get_index(folder_id)

            if index is None:
                raise ValueError(f"No index found for folder ID: {folder_id}")

            # Set up retriever and post-processor
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=self.top_k,
            )

            # Use similarity score cutoff to filter out irrelevant results
            postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)

            # Create response synthesizer
            response_synthesizer = get_response_synthesizer(
                llm=self.llm,
                response_mode="refine",
            )

            # Create the query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer,
                node_postprocessors=[postprocessor],
            )

            # Execute query
            response = query_engine.query(query_text)

            # Extract source documents
            source_documents = []
            for source_node in response.source_nodes:
                source_doc = {
                    "text": source_node.text,
                    "score": source_node.score,
                    "file_name": source_node.metadata.get("file_name", "Unknown"),
                    "file_id": source_node.metadata.get("file_id", "Unknown"),
                    "mime_type": source_node.metadata.get("mime_type", "Unknown"),
                }
                source_documents.append(source_doc)

            return response.response, source_documents
        except Exception as e:
            print(f"Error in QueryEngine.query: {str(e)}")
            import traceback

            traceback.print_exc()
            raise

    def query_with_feedback(
        self, query_text: str, folder_id: str, feedback: str = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query with user feedback for improved answers.

        Args:
            query_text: User query text
            folder_id: Google Drive folder ID to query against
            feedback: Optional user feedback from previous query

        Returns:
            Tuple of (answer_text, source_documents)
        """
        # Incorporate feedback into the query if provided
        if feedback:
            enhanced_query = f"Original query: {query_text}\nUser feedback: {feedback}\nPlease provide an improved answer based on this feedback."
        else:
            enhanced_query = query_text

        # Use the regular query method
        return self.query(enhanced_query, folder_id)
