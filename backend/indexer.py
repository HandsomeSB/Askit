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

# These metadata fields would be included in the text before embedding
EMBEDDING_METADATA = [
    "title",  # Document titles often contain important context
    "author",  # Author names can be semantically relevant
    "subject",  # Subject/topic information
    "description",  # Any file descriptions
    "keywords",  # Keywords/tags
    "location_name",  # For images/videos (not coordinates)
    "camera_model",  # For images (as it might indicate quality/type)
    "file_type",  # General file type (document, image, etc.)
]

# These would remain as structured data for precise filtering
FILTERING_METADATA = [
    "created_time",  # For date range filtering
    "modified_time",  # For date range filtering
    "file_size",  # For size filtering
    "dimensions",  # For image/video size filtering
    "duration",  # For media length filtering
    "coordinates",  # For precise location filtering
    "page_count",  # For document length filtering
    "bitrate",  # For media quality filtering
]


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

    def _enhance_content_with_metadata(self, document: Document) -> Document:
        """
        Enhance document content with relevant metadata for embedding.

        Args:
            document: Original document

        Returns:
            Enhanced document with metadata in content
        """
        metadata = document.metadata
        enhanced_content = []

        # Add relevant metadata to content
        for field in EMBEDDING_METADATA:
            if field in metadata and metadata[field]:
                if isinstance(metadata[field], list):
                    enhanced_content.append(f"{field}: {', '.join(metadata[field])}")
                else:
                    enhanced_content.append(f"{field}: {metadata[field]}")

        # Add original content
        enhanced_content.append("\nContent:")
        enhanced_content.append(document.text)

        # Create new document with enhanced content
        return Document(
            text="\n".join(enhanced_content),
            metadata=document.metadata,  # Keep original metadata for filtering
        )

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

        # Enhance documents with metadata
        enhanced_documents = [
            self._enhance_content_with_metadata(doc) for doc in documents
        ]

        # Parse documents into nodes (chunks)
        nodes = self.node_parser.get_nodes_from_documents(enhanced_documents)

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
