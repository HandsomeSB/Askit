from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.storage.storage_context import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding

import os

from document_processor import get_docs, get_file_paths
# Initialize OpenAI embedding model
embedding_model = OpenAIEmbedding()

vector_store = SimpleVectorStore()
os.makedirs("storage", exist_ok=True)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

def embed_folder(folder_path):
    file_paths = get_file_paths(folder_path)
    docs = get_docs(file_paths)
    # Build the index; this splits docs into metadata‑rich chunks and embeds them
    index = VectorStoreIndex.from_documents(docs, storage_context=storage_context, embed_model=embedding_model)
    index.storage_context.persist(persist_dir="storage")
    return index

def load_index():
    # Load the index from the storage context
    index = VectorStoreIndex.load_from_storage(storage_context=storage_context)
    return index
