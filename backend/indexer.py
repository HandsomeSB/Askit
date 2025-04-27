import os
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
import pymongo
from pymongo.operations import SearchIndexModel

load_dotenv()

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.storage.storage_context import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.core.ingestion import IngestionPipeline
from llama_index.storage.docstore.mongodb import MongoDocumentStore


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
        self.mongo_client = pymongo.MongoClient(os.getenv("MONGODB_URI"))

        os.makedirs(persist_dir, exist_ok=True)

        self.vector_store = SimpleVectorStore()

    # NOTE, Use index.refresh_ref_docs
    def create_index(self, documents: List[Document], folder_id: str, absolute_id_path: str) -> VectorStoreIndex:
        """Convert documents to index and save to disk."""
        root_id = absolute_id_path.strip("/").split("/")[0]
        if documents:
            vector_store = MongoDBAtlasVectorSearch(
                self.mongo_client,
                db_name = "llamaindex_db",
                collection_name = root_id,
                vector_index_name = "vector_index"
            )

            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            collection = self.mongo_client["llamaindex_db"][root_id]
            existing = list(collection.list_search_indexes())
            # existing_names = { idx.document["name"] for idx in existing }
            # print("Existing search indexes:", existing_names)
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": 1536,
                            "similarity": "cosine"
                        },
                        {
                            "type": "filter",
                            "path": "metadata.absolute_path",
                        }
                    ]
                },
                name="vector_index",
                type="vectorSearch"
                )
            if search_index_model not in existing:
                try:
                    collection.create_search_index(model=search_index_model)
                    print("Search index created successfully.")
                except Exception as e:
                    print("Failed to create search index:", e)
            else:
                print(f"🔍 Search index {search_index_model.name} already exists – skipping.")
            
            for doc in documents:
                doc.metadata["absolute_path"] = absolute_id_path

            # nodes = self.node_parser.get_nodes_from_documents(documents)

            # index = VectorStoreIndex(
            #     nodes, 
            #     storage_context=storage_context, 
            #     embed_model=self.embedding_model,
            #     show_progress=True,
            # )
            docstore = MongoDocumentStore.from_uri(
                uri=os.getenv("MONGODB_URI"),
                db_name="llamaindex_db",
                namespace=root_id,
            )

            pipeline = IngestionPipeline(
                transformations=[
                    self.node_parser,
                    OpenAIEmbedding(model_name="text-embedding-ada-002"),
                ],
                docstore=docstore,
                vector_store=vector_store,
                # <-- the magic bit:
                docstore_strategy="upserts",
            )

            pipeline.run(documents=documents, show_progress=True)

            # Save folder wise metadata
            metadata = {
                "folder_id": folder_id,
                "absolute_path": absolute_id_path,
                "time_indexed": datetime.now().isoformat(),
            }

        # NOTE, Change implementation for database
        # _save_metadata(metadata, absolute_id_path)
        self.mongo_client["llamaindex_db"][f"{root_id}/index_metadata"].update_one(
            {"folder_id": folder_id},  # filter to find document
            {"$set": metadata},        # update with new metadata
            upsert=True                # insert if not found
        )

        # return index

    def get_index(self, root_id: str):
        vector_store = MongoDBAtlasVectorSearch(
            self.mongo_client,
            db_name = "llamaindex_db",
            collection_name = root_id,
            vector_index_name = "vector_index"
        )

        # storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=self.embedding_model,   # e.g. OpenAIEmbedding(model="text-embedding-ada-002")
            show_progress=True                  # optional
        )

    
    def delete_index(self, folder_id: str) -> bool:
        pass

    def get_index_structure(self, root_id: str) -> List[Dict[str, Any]]:
        """Get the index structure of the folder."""
        # Note: folder_id parameter may not be used if we're retrieving all metadata
        collection = self.mongo_client["llamaindex_db"][f"{root_id}/index_metadata"]

        documents = list(collection.find({}))
        result = []
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]  # Remove MongoDB's internal ID
            result.append(doc)
        
        return result

def _get_index_structure(start_path: str) -> List[Dict[str, Any]]:
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
            dir_info["children"] = _get_index_structure(item_path)  # Recursively process subdirectories
            
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
