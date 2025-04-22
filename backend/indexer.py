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

import google_drive_utils
from datetime import datetime

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
            chunk_size=512,
            chunk_overlap=48, 
            embed_model=self.embedding_model
        )

        os.makedirs(persist_dir, exist_ok=True)

        self.vector_store = SimpleVectorStore()

    # NOTE, Use index.refresh_ref_docs
    def create_index(self, documents: List[Document], folder_id: str, absolute_id_path: str) -> VectorStoreIndex:
        """Convert documents to index and save to disk."""
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        nodes = self.node_parser.get_nodes_from_documents(documents)

        index = VectorStoreIndex(
            nodes, 
            storage_context=storage_context, 
            embed_model=self.embedding_model,
        )

        # Save folder wise metadata
        metadata = {
            "folder_id": folder_id,
            "absolute_path": absolute_id_path,
            "time_indexed": datetime.now().isoformat(),
        }

        # NOTE, Change implementation for database
        _save_metadata(metadata, absolute_id_path)

        index.storage_context.persist(persist_dir=self.persist_dir + f"/{absolute_id_path}")
        return index

    def get_index(self, folder_id: str):
        """Load index from disk. Return a list of indices."""
        print(folder_id)
        index_path = _find_subdirectory(self.persist_dir, folder_id)
        print(index_path)

        storage_context = StorageContext.from_defaults(persist_dir=index_path)
        index = load_index_from_storage(storage_context=storage_context)

        subindices = _get_subindices(index_path)
        subindices.append(index)
        
        return subindices
    
    def delete_index(self, folder_id: str) -> bool:
        pass

    # NOTE, Change implementation for database
    def get_index_structure(self, start_path: str) -> List[Dict[str, Any]]:
        """Get the index structure of the folder."""
        result = []
        
        if not os.path.exists(start_path):
            return result

        # Loop through all directories within the start path
        for item in os.listdir(start_path):
            item_path = os.path.join(start_path, item)
            
            if os.path.isdir(item_path):
                # Check for metadata file
                metadata_path = os.path.join(item_path, "metadata.json")
                metadata = {}
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                    except json.JSONDecodeError:
                        # Handle invalid metadata files
                        pass
                
                # Create node for this directory
                dir_info = metadata.copy()
                dir_info["children"] = self.get_index_structure(item_path)  # Recursively process subdirectories
                
                result.append(dir_info)

        return result


def _find_subdirectory(base_dir: str, target_dir: str) -> str:
    """
    Search for a subdirectory with the name target_dir within base_dir.
    If found, return the full path to that subdirectory.
    If not found, raise a FileNotFoundError.
    Args:
        base_dir (str): The base directory to search in.
        target_dir (str): The name of the subdirectory to find.
    Returns:
        str: The full path to the found subdirectory.
    """
    index_path = None

    # Search for a directory with name equal to folder_id
    for root, dirs, _ in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name == target_dir:
                index_path = os.path.join(root, dir_name)
                break  # Exit the inner loop once found
        if index_path:
            break  # Exit the outer loop once found

    if not index_path:
        # If no matching directory is found, raise an error
        raise FileNotFoundError(f"No index found for folder ID: {target_dir}")
    
    return index_path

def _get_subindices(base_dir):
    subindices = []

    # Search for all directories in the base directory
    for root, dirs, _ in os.walk(base_dir):
        for dir_name in dirs:
            path = os.path.join(root, dir_name)
            try:
                storage_context = StorageContext.from_defaults(persist_dir=path)
                index = load_index_from_storage(storage_context=storage_context)
                subindices.append(index)
            except:
                continue
            subindices.extend(_get_subindices(path))

    return subindices

def _save_metadata(metadata: Dict[str, Any], absolute_id_path: str):
    """Save metadata to disk."""
    os.makedirs(f"./storage/{absolute_id_path}", exist_ok=True)
    with open(f"./storage/{absolute_id_path}/metadata.json", "w") as f:
        json.dump(metadata, f)