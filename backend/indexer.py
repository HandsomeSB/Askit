import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.storage.storage_context import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

EMBEDDING_METADATA = [
    "title",
    "author",
    "subject",
    "description",
    "keywords",
    "location_name",
    "camera_model",
    "file_type",
]

FILTERING_METADATA = [
    "created_time",
    "modified_time",
    "file_size",
    "dimensions",
    "duration",
    "coordinates",
    "page_count",
    "bitrate",
]


class DocumentIndexer:
    def __init__(self, persist_dir: str = "./storage"):
        self.persist_dir = persist_dir
        self.embedding_model = OpenAIEmbedding()
        self.node_parser = SemanticSplitterNodeParser(
            chunk_size=1024,
            embed_model=self.embedding_model
        )

        os.makedirs(persist_dir, exist_ok=True)

        self.vector_store = SimpleVectorStore()
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def create_index(self, documents: List[Document], folder_id: str) -> VectorStoreIndex:
        """Convert documents to index and save to disk."""
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=self.storage_context, 
            embed_model=self.embedding_model
        )
        index.storage_context.persist(persist_dir=self.persist_dir)
        return index

    def get_index(self, folder_id: str):
        """Load index from disk."""
        # NOTE: Later, we will use the folder_id to filter the index
        index = VectorStoreIndex.load_from_storage(storage_context=self.storage_context)
        return index
    
    def delete_index(self, folder_id: str) -> bool:
        pass