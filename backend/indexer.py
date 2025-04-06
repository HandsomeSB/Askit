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
        self.node_parser = SemanticSplitterNodeParser(chunk_size=1024)

        os.makedirs(persist_dir, exist_ok=True)

        self.index_map_path = os.path.join(persist_dir, "index_map.json")
        self.folder_to_index_map = self._load_index_map()
        self.indices = {}

    def _load_index_map(self) -> Dict[str, str]:
        if os.path.exists(self.index_map_path):
            with open(self.index_map_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _save_index_map(self):
        with open(self.index_map_path, "w") as f:
            json.dump(self.folder_to_index_map, f)

    def _enhance_content_with_metadata(self, document: Document) -> Document:
        metadata = document.metadata
        enhanced_content = []
        MAX_METADATA_BLOCK_LENGTH = 800

        meta_lines = []
        for field in EMBEDDING_METADATA:
            if field in metadata and metadata[field]:
                value = metadata[field]
                if isinstance(value, list):
                    value = ", ".join(value)
                value = str(value)
                meta_lines.append(f"{field}: {value}")

        metadata_text = "\n".join(meta_lines)
        if len(metadata_text) > MAX_METADATA_BLOCK_LENGTH:
            metadata_text = metadata_text[:MAX_METADATA_BLOCK_LENGTH] + "..."

        final_text = f"{metadata_text}\n\nContent:\n{document.text}"

        return Document(
            text=final_text,
            metadata=document.metadata,
        )

    def create_index(self, documents: List[Document], folder_id: str) -> str:
        index_id = f"index_{folder_id.replace('-', '_')}"
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        enhanced_documents = [
            self._enhance_content_with_metadata(doc) for doc in documents
        ]
        nodes = self.node_parser.get_nodes_from_documents(enhanced_documents)

        index = VectorStoreIndex(
            nodes, storage_context=storage_context, embed_model=self.embedding_model
        )

        self.folder_to_index_map[folder_id] = index_id
        self.indices[folder_id] = index
        self._save_index_map()

        index_dir = os.path.join(self.persist_dir, index_id)
        os.makedirs(index_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=index_dir)

        return index_id

    def get_index(self, folder_id: str):
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
        except Exception:
            del self.folder_to_index_map[folder_id]
            self._save_index_map()
            return None

    def delete_index(self, folder_id: str) -> bool:
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
        except Exception:
            del self.folder_to_index_map[folder_id]
            if folder_id in self.indices:
                del self.indices[folder_id]
            self._save_index_map()
            return False
