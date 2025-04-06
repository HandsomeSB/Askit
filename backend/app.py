# app.py - Main application entry point
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from document_processor import DocumentProcessor
from indexer import DocumentIndexer
from query_engine import EnhancedQueryEngine

app = FastAPI(title="Document Retrieval System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    document_processor = DocumentProcessor()
    document_indexer = DocumentIndexer()
    query_engine = EnhancedQueryEngine()
    print("Successfully initialized all components")
except Exception as e:
    print(f"Error initializing components: {str(e)}")
    import traceback

    traceback.print_exc()
    # We'll initialize them as None and handle it in the endpoints
    document_processor = None
    document_indexer = None
    query_engine = None


class QueryRequest(BaseModel):
    query: str
    folder_id: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class ProcessFolderRequest(BaseModel):
    folder_id: str


@app.post("/api/process-folder")
async def process_folder(request: ProcessFolderRequest):
    """
    Process all files in a Google Drive folder and create an index.

    Args:
        request: ProcessFolderRequest containing the folder_id

    Returns:
        Dict with processing status and index_id
    """
    try:
        # Check if document processor is initialized
        if document_processor is None:
            raise HTTPException(
                status_code=500,
                detail="Document processor not initialized. Please check server logs for details.",
            )

        if not request.folder_id:
            raise HTTPException(status_code=400, detail="folder_id is required")

        # Get all files from the folder
        try:
            files = document_processor.get_files_from_drive(request.folder_id)
        except Exception as drive_error:
            print(f"Error accessing Google Drive: {str(drive_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to access Google Drive: {str(drive_error)}",
            )

        # Process each file and convert to documents
        documents = []
        for file in files:
            try:
                file_documents = document_processor.process_file(file)
                documents.extend(file_documents)
            except Exception as file_error:
                print(
                    f"Error processing file {file.get('name', 'unknown')}: {str(file_error)}"
                )
                continue

        if not documents:
            raise HTTPException(
                status_code=500,
                detail="No documents were successfully processed from the folder",
            )

        # Create index from documents
        try:
            index_id = document_indexer.create_index(documents, request.folder_id)
        except Exception as index_error:
            print(f"Error creating index: {str(index_error)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create index: {str(index_error)}"
            )

        return {
            "status": "success",
            "message": f"Processed {len(files)} files",
            "index_id": index_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f"Unexpected error in process_folder: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the system with a question, restricted to a specific folder.

    Args:
        request: QueryRequest containing the query text and folder_id

    Returns:
        QueryResponse with answer and source documents
    """
    try:
        # Check if query engine is initialized
        if query_engine is None:
            raise HTTPException(
                status_code=500,
                detail="Query engine not initialized. Please check server logs for details.",
            )

        # Get the answer and sources
        try:
            answer, sources = query_engine.query(request.query, request.folder_id)
            return QueryResponse(answer=answer, sources=sources)
        except Exception as query_error:
            print(f"Error in query_engine.query: {str(query_error)}")
            import traceback

            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail=f"Error processing query: {str(query_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in query endpoint: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/auth/google-drive")
async def authenticate_google_drive():
    """
    Authenticate with Google Drive and return the authentication status.
    """
    try:
        if document_processor is None:
            raise HTTPException(
                status_code=500,
                detail="Document processor not initialized. Please check server logs for details.",
            )

        # The DocumentProcessor class already handles authentication
        # If we get here, it means authentication was successful
        return {
            "status": "success",
            "message": "Successfully authenticated with Google Drive",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/folders")
async def get_drive_folders():
    """
    Get all folders from the user's Google Drive.
    """
    try:
        if document_processor is None:
            raise HTTPException(
                status_code=500,
                detail="Document processor not initialized. Please check server logs for details.",
            )

        try:
            # Query for all folders in Drive
            response = (
                document_processor.drive_service.files()
                .list(
                    q="mimeType='application/vnd.google-apps.folder'",
                    spaces="drive",
                    fields="files(id, name)",
                    pageSize=100,
                )
                .execute()
            )

            folders = response.get("files", [])

            # Format the response
            formatted_folders = [
                {"id": folder["id"], "name": folder["name"]} for folder in folders
            ]

            return formatted_folders
        except Exception as e:
            print(f"Error fetching folders: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch folders: {str(e)}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
