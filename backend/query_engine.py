from typing import List, Dict, Any, Tuple, Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field
import json

# Load environment variables from .env file
load_dotenv()

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.llms import ChatMessage
from llama_index.llms.gemini import Gemini
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterCondition

from indexer import DocumentIndexer, FILTERING_METADATA

from enum import Enum
from typing import Literal

MetaFilters = {
    "created_time_before": lambda date: 
        MetadataFilter(key="created_time", operator=">=", value=datetime(2025,4,1).isoformat()),
    "created_time_after": lambda date:
        MetadataFilter(key="created_time", operator="<=", value=datetime(2025,4,1).isoformat()),
    "page_count_equal": lambda count:
        MetadataFilter(key="page_count", operator="==", value=count),
    "None": lambda _: None,
}

FilterType = Literal[*MetaFilters.keys()]

class QueryParams(BaseModel):
    """Data model for a retriever parameter."""
    @staticmethod
    def get_description() -> str:
        desc = f"""
        refined_prompt: The refined prompt to be used for the query.
        threshold: The threshold for filtering results based on similarity.
            the threshold is a float value between 0 and 1. Keep the threshold 
            low if the query is very broad, keep the threshold high if the query is
            specific. 

            Example: Query: "Find me any files related to the project"
            threshold: 0.4

            Example: Query: "Find me the project report for the last quarter"
            threshold: 0.5

            Example: Query: "What is the military industrial complex?"
            threshold: 0.7
        """
        """ NOTE, Commented out for now
        filter_type: The type of meta data filter to be applied to the results. 
        filter_kwargs: The arguments to be passed to the filter function.
            The filter_type is a string value that can be one of the following:
            {MetaFilters.keys()}.
            The filter_kwargs is a dictionary that contains the arguments to be passed:
            created_time_before: date: The date to filter the results by.
            created_time_after: date: The date to filter the results by.
            page_count_equal: count: The page count to filter the results by.
            None: No filter to be applied.
            
            Example: Query: "Find me any files related to the project"
            filter_type: None
            filter_kwargs: None

            Example: Query: "Find me the project report for the last quarter"
            filter_type: created_time_before
            filter_kwargs: date: 2025-04-01

            Example: Query: "Which document about the US has two pages?"
            filter_type: page_count_equal
            filter_kwargs: count : 2

            Example: Query: "Which document about the US has the most pages"
            filter_type: None
            filter_kwargs: None
            
        """
        return desc

    refined_prompt: str
    # filter_type: FilterType # Ignore the warning
    # filter_kwargs: Dict[str, Any]
    threshold: float

class EnhancedQueryEngine:
    def __init__(self, top_k: int = 10, similarity_threshold: float = 0.78):
        self.document_indexer = DocumentIndexer()
        self.llm = Gemini(model="models/gemini-1.5-flash")
        self.refiner = Gemini(model="models/gemini-1.5-flash").as_structured_llm(output_cls=QueryParams)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def _refine_prompt(self, query_text: str) -> str:
        """Refine the prompt using the LLM."""
        input_msg = ChatMessage.from_str(
            f"""
            You are an expert in document retrieval and natural language processing.
            Your task is to refine a user query to make it more specific and relevant for document retrieval.
            This app is designed to find the most relevant documents given an arbitrary user query.
            Refine the following query to make it more specific and improve document retrieval: {query_text}
            
            Here are some necessary context to determine your output: {QueryParams.get_description()}
            """
        )
        response = self.refiner.chat([input_msg])
        return response.raw

    def query(
        self, query_text: str, folder_id: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        indices = self.document_indexer.get_index(folder_id)
        
        query_params = self._refine_prompt(query_text)

        retrievers = [idx.as_retriever(
            # similarity_cutoff=min(self.similarity_threshold, query_params.threshold),
            similarity_cutoff=self.similarity_threshold # NOTE, threshold turned off for now
        ) for idx in indices]

        retriever = QueryFusionRetriever(
            retrievers,
            similarity_top_k=self.top_k,
            use_async=False,
        )

        results = retriever.retrieve(query_params.refined_prompt)
        # print(query_params.filter_type)
        # print(query_params.filter_kwargs)

        if not results:
            return (
                "I couldn't find any relevant documents in your folder to answer this question. Please make sure the documents you're looking for are in the selected folder and try again.",
                [],
            )

        context = "\n\n".join([f"[Document: {node.text} Meta: {json.dumps(node.metadata)}]" for node in results])
        prompt = f"""Based on the following documents, 
        please provide a comprehensive answer to the question: {query_text}
        Documents: {context}
        Please provide a very concise answer that synthesizes information 
        from the relevant documents. If the documents don't contain enough 
        information to answer the question, please say so."""

        answer = self.llm.complete(prompt).text

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
