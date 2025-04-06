import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()

from llama_index.core import Document, VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

from document_processor import DocumentProcessor

from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
import pymongo

mongodb_uri = os.getenv("MONGODB_URI")
mongodb_client = pymongo.MongoClient(mongodb_uri, serverSelectionTimeoutMS=60000)
db_name = "askit"
collection_name = "embeddings"
# collection = mongodb_client[db_name][collection_name]

print(mongodb_client[db_name].list_collection_names())


# atlas_vector_store = MongoDBAtlasVectorSearch(
#     mongodb_client,
#     db_name = "askit",
#     collection_name = "embeddings",
#     vector_index_name = "vector_index"
# )
# vector_store_context = StorageContext.from_defaults(vector_store=atlas_vector_store)


# Constants for metadata categorization
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
        """
        Initialize document indexer with embedding model and node parser.
        
        Args:
            persist_dir: Directory to store the index
        """
        self.persist_dir = persist_dir
        self.embedding_model = OpenAIEmbedding(model="text-embedding-ada-002")
        
        # Custom text splitter with defined chunk size and overlap
        self.node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
        )

        # Create storage directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)

        # Load index map from persistence
        self.index_map_path = os.path.join(persist_dir, "index_map.json")
        self.folder_to_index_map = self._load_index_map()
        self.indices = {}
        
        # Initialize document processor
        self.document_processor = DocumentProcessor()
        if not self.document_processor.drive_service:
            self.document_processor.drive_service = self.document_processor._setup_drive_connection()

    def _load_index_map(self) -> Dict[str, str]:
        """Load the index map from disk"""
        if os.path.exists(self.index_map_path):
            with open(self.index_map_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _save_index_map(self):
        """Save the index map to disk"""
        with open(self.index_map_path, "w") as f:
            json.dump(self.folder_to_index_map, f)

    def process_and_index_drive_folder(self, folder_id: str) -> str:
        """
        Process files from a Google Drive folder and create an index.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            index_id: ID of the created index
        """
        # Get files from Google Drive folder
        file_list = self.document_processor.get_files_from_drive(folder_id)
        
        # Process files and convert to documents
        all_documents = []
        for file_metadata in file_list:
            documents = self.document_processor.process_file(file_metadata)
            all_documents.extend(documents)
            
        # Create index from the documents
        return self.create_index(all_documents, folder_id)

    def create_index(self, documents: List[Document], folder_id: str) -> str:
        """
        Create a vector index from documents.
        
        Args:
            documents: List of documents to index
            folder_id: ID of the folder being indexed
            
        Returns:
            index_id: ID of the created index
        """
        index_id = f"index_{folder_id.replace('-', '_')}"
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Get nodes from documents using the configured splitter
        nodes = self.node_parser.get_nodes_from_documents(documents)
        
        # Add metadata to each node before indexing
        for node in nodes:
            # Preserve existing metadata
            file_metadata = node.metadata
            
            # Standardize and enhance metadata
            enhanced_metadata = {
                "file_id": file_metadata.get("file_id", ""),
                "file_name": file_metadata.get("file_name", ""),
                "file_type": os.path.splitext(file_metadata.get("file_name", ""))[1].replace(".", "") if "file_name" in file_metadata else "",
                "author": file_metadata.get("author", ""),
                "created_time": file_metadata.get("created_time", ""),
                "modified_time": file_metadata.get("modified_time", ""),
                "mime_type": file_metadata.get("mime_type", ""),
                "web_view_link": file_metadata.get("web_view_link", ""),
                "thumbnail_link": file_metadata.get("thumbnail_link", ""),
            }
            
            # Add any additional metadata from the original
            for key, value in file_metadata.items():
                if key not in enhanced_metadata:
                    enhanced_metadata[key] = value
                    
            # Update node metadata
            node.metadata = enhanced_metadata

        # Create vector store index with the nodes
        index = VectorStoreIndex(
            nodes, 
            storage_context=storage_context,
            embed_model=self.embedding_model
        )

        # Save mappings and index
        self.folder_to_index_map[folder_id] = index_id
        self.indices[folder_id] = index
        self._save_index_map()

        # Persist index to disk
        index_dir = os.path.join(self.persist_dir, index_id)
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)

        return index_id

    def get_index(self, folder_id: str):
        """
        Get index for a folder ID.
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            index: Vector store index or None if not found
        """
        if folder_id not in self.folder_to_index_map:
            return None

        if folder_id in self.indices:
            return self.indices[folder_id]

        index_id = self.folder_to_index_map[folder_id]
        index_dir = os.path.join(self.persist_dir, index_id)

        try:
            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            index = load_index_from_storage(
                storage_context=storage_context, embed_model=self.embedding_model
            )

            self.indices[folder_id] = index
            return index
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            del self.folder_to_index_map[folder_id]
            self._save_index_map()
            return None

    def delete_index(self, folder_id: str) -> bool:
        """
        Delete an index for a folder.
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            success: True if deleted successfully
        """
        if folder_id not in self.folder_to_index_map:
            return False

        index_id = self.folder_to_index_map[folder_id]
        index_dir = os.path.join(self.persist_dir, index_id)

        try:
            if os.path.exists(index_dir):
                import shutil
                shutil.rmtree(index_dir)

            del self.folder_to_index_map[folder_id]
            if folder_id in self.indices:
                del self.indices[folder_id]
            self._save_index_map()

            return True
        except Exception as e:
            print(f"Error deleting index: {str(e)}")
            del self.folder_to_index_map[folder_id]
            if folder_id in self.indices:
                del self.indices[folder_id]
            self._save_index_map()
            return False

    def save_index_to_mongodb(self, documents: List[Document]):
        """
        Save the index to MongoDB Atlas Vector Search.
        """
        # Create index with the storage context
        # index = VectorStoreIndex.from_documents(
        #     documents, 
        #     storage_context=storage_context,
        # )
        pass

    

