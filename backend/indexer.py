# indexer.py
import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding


class DocumentIndexer:
    """
    Create and manage document indices for efficient retrieval.
    Uses SimpleVectorStore for vector storage and OpenAI embeddings.
    """

    def __init__(self, persist_dir: str = "./storage"):
        """
        Initialize document indexer.

        Args:
            persist_dir: Directory to persist indices
        """
        self.persist_dir = persist_dir
        self.embedding_model = OpenAIEmbedding()
        self.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)

        # Create storage directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)

        # Keep a record of folder to index mappings
        self.index_map_path = os.path.join(persist_dir, "index_map.json")
        self.folder_to_index_map = self._load_index_map()
        self.indices = {}  # Cache for loaded indices

    def _load_index_map(self) -> Dict[str, str]:
        """
        Load the folder to index mapping from disk.

        Returns:
            Dictionary mapping folder IDs to index IDs
        """
        if os.path.exists(self.index_map_path):
            with open(self.index_map_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _save_index_map(self):
        """Save the folder to index mapping to disk."""
        with open(self.index_map_path, "w") as f:
            json.dump(self.folder_to_index_map, f)

    def create_index(self, documents: List[Document], folder_id: str) -> str:
        """
        Create an index from a list of documents.

        Args:
            documents: List of LlamaIndex Document objects
            folder_id: Google Drive folder ID

        Returns:
            Index ID
        """
        # Create a new index ID based on folder ID
        index_id = f"index_{folder_id.replace('-', '_')}"

        # Create vector store and storage context
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Parse documents into nodes (chunks)
        nodes = self.node_parser.get_nodes_from_documents(documents)

        # Create the index
        index = VectorStoreIndex(
            nodes, storage_context=storage_context, embed_model=self.embedding_model
        )

        # Store in our folder to index map and cache
        self.folder_to_index_map[folder_id] = index_id
        self.indices[folder_id] = index
        self._save_index_map()

        # Save the index
        index_dir = os.path.join(self.persist_dir, index_id)
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)

        return index_id

    def get_index(self, folder_id: str):
        """
        Get an index for a specific folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            VectorStoreIndex object or None if not found
        """
        if folder_id not in self.folder_to_index_map:
            return None

        # Check if index is in cache
        if folder_id in self.indices:
            return self.indices[folder_id]

        index_id = self.folder_to_index_map[folder_id]
        index_dir = os.path.join(self.persist_dir, index_id)

        try:
            # Load the index from disk
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(
                storage_context=storage_context, embed_model=self.embedding_model
            )

            # Cache the loaded index
            self.indices[folder_id] = index
            return index
        except Exception:
            # Index doesn't exist or is corrupted
            del self.folder_to_index_map[folder_id]
            self._save_index_map()
            return None

    def delete_index(self, folder_id: str) -> bool:
        """
        Delete an index for a specific folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            True if successful, False otherwise
        """
        if folder_id not in self.folder_to_index_map:
            return False

        index_id = self.folder_to_index_map[folder_id]
        index_dir = os.path.join(self.persist_dir, index_id)

        try:
            # Remove the index directory
            if os.path.exists(index_dir):
                import shutil

                shutil.rmtree(index_dir)

            # Remove from our mapping and cache
            del self.folder_to_index_map[folder_id]
            if folder_id in self.indices:
                del self.indices[folder_id]
            self._save_index_map()

            return True
        except Exception:
            # Something went wrong
            del self.folder_to_index_map[folder_id]
            if folder_id in self.indices:
                del self.indices[folder_id]
            self._save_index_map()
            return False
