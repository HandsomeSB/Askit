# app.py - Main application entry point with session architecture
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import secrets
import json
import time
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
# Rename the imported Request to avoid conflict
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

from document_processor import DocumentProcessor
from indexer import DocumentIndexer
from query_engine import QueryEngine

app = FastAPI(title="Document Retrieval System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    # Generate a temporary secret key for development only
    # In production, this should be set in environment variables
    SESSION_SECRET_KEY = secrets.token_hex(32)
    print(f"WARNING: Using temporary session key: {SESSION_SECRET_KEY}")
    print("Set SESSION_SECRET_KEY in environment for production")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=3600,  # 1 hour session timeout
)

# Store for temporary auth states
auth_states = {}

# Initialize components
try:
    document_processor = DocumentProcessor()
    document_indexer = DocumentIndexer()
    query_engine = QueryEngine()
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


# OAuth Endpoints for Frontend Authentication Flow
@app.get("/api/auth/google-url")
async def get_auth_url(request: Request):
    """Generate Google OAuth URL for frontend to redirect to"""
    # Generate a random state token to prevent CSRF attacks
    state = secrets.token_urlsafe(16)
    
    # Store state with timestamp (for expiration)
    auth_states[state] = {"created_at": time.time()}
    
    # Clean up expired states (older than 10 minutes)
    current_time = time.time()
    expired_states = [s for s in auth_states if current_time - auth_states[s]["created_at"] > 600]
    for s in expired_states:
        del auth_states[s]
    
    # Create OAuth flow with redirect to frontend
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
        redirect_uri="http://localhost:3000/auth/callback"  # Frontend URL
    )
    
    # Get authorization URL with state parameter
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        state=state,
        include_granted_scopes="true",
        prompt="consent"
    )
    
    return {"auth_url": auth_url}


@app.post("/api/auth/google-callback")
async def auth_callback(request: Request, code: str, state: str):
    """Handle OAuth callback from frontend"""
    # Verify state to prevent CSRF
    if state not in auth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    
    # Clean up state
    del auth_states[state]
    
    # Create flow with same redirect URI
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
        redirect_uri="http://localhost:3000/auth/callback"
    )
    
    # Exchange authorization code for tokens
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials in session
        request.session["credentials"] = credentials.to_json()
        
        # Generate a session ID for the frontend
        session_id = secrets.token_urlsafe(32)
        request.session["session_id"] = session_id
        
        return {"session_id": session_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange auth code: {str(e)}")


# Dependency to get drive service with user credentials
async def get_drive_service(request: Request):
    """Get Google Drive service for authenticated user"""
    credentials_json = request.session.get("credentials")
    if not credentials_json:
        raise HTTPException(status_code=401, detail="Not authenticated with Google Drive")
    
    try:
        credentials = Credentials.from_json(credentials_json)
        
        # Check if credentials expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleAuthRequest())
            # Update session with refreshed credentials
            request.session["credentials"] = credentials.to_json()
        
        # Build and return the drive service
        drive_service = build("drive", "v3", credentials=credentials)
        return drive_service
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


@app.post("/api/process-folder")
async def process_folder(request: Request, folder_request: ProcessFolderRequest):
    """
    Process all files in a Google Drive folder and create an index.
    Uses the authenticated user's credentials.
    """
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        if not folder_request.folder_id:
            raise HTTPException(status_code=400, detail="folder_id is required")
        
        # Create a DocumentProcessor with the user's drive service
        user_document_processor = DocumentProcessor(drive_service=drive_service)
        
        # Get all files from the folder
        try:
            files = user_document_processor.get_files_from_drive(folder_request.folder_id)
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
                file_documents = user_document_processor.process_file(file)
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
        
        # Store session ID with the documents for user identification
        session_id = request.session.get("session_id", "anonymous")
        for doc in documents:
            doc.metadata["session_id"] = session_id
        
        # Create index from documents
        try:
            index_id = document_indexer.create_index(documents, folder_request.folder_id, user_id=session_id)
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
async def query(request: Request, query_request: QueryRequest):
    """
    Query the system with a question, restricted to a specific folder.
    Uses the authenticated user's session.
    """
    try:
        # Check if authenticated
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Check if query engine is initialized
        if query_engine is None:
            raise HTTPException(
                status_code=500,
                detail="Query engine not initialized. Please check server logs for details.",
            )
        
        # Get the answer and sources
        try:
            # Pass user ID (session_id) to restrict queries to user's own indices
            answer, sources = query_engine.query(
                query_request.query, 
                query_request.folder_id,
                user_id=session_id
            )
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


@app.get("/api/auth/check")
async def check_auth(request: Request):
    """
    Check if user is authenticated.
    """
    try:
        credentials_json = request.session.get("credentials")
        if not credentials_json:
            return {"authenticated": False}
        
        # Try to parse credentials to verify they're valid
        credentials = Credentials.from_json(credentials_json)
        
        # Return basic user info
        return {
            "authenticated": True,
            "session_id": request.session.get("session_id", "unknown"),
            "expires": credentials.expiry.isoformat() if credentials.expiry else None
        }
    except Exception as e:
        print(f"Error checking authentication: {str(e)}")
        return {"authenticated": False, "error": str(e)}


@app.post("/api/auth/logout")
async def logout(request: Request):
    """
    Log out the current user by clearing their session.
    """
    try:
        # Clear session data
        request.session.clear()
        return {"success": True, "message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during logout: {str(e)}")


@app.get("/api/folders")
async def get_drive_folders(request: Request):
    """
    Get all folders from the authenticated user's Google Drive.
    """
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        # Get the root folder ID (this is the user's Drive root)
        root_folder_id = "root"
        
        # Query files within the specified folder
        query = f"mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        files = []
        page_token = None
        
        while True:
            response = (
                drive_service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token,
                )
                .execute()
            )
            
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            
            if not page_token:
                break
        
        # Format the response
        formatted_folders = [
            {"id": folder["id"], "name": folder["name"]} for folder in files
        ]
        
        return formatted_folders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)