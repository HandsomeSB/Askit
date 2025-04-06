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
from localJsonStore import LocalJsonStore

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
    same_site="lax",  # Important for cross-site requests
    https_only=False,  # Set to True in production with HTTPS
)

# Store for temporary auth states
auth_states = {}

# Initialize components
try:
    document_indexer = DocumentIndexer()
    query_engine = EnhancedQueryEngine()
    print("Successfully initialized all components")
except Exception as e:
    print(f"Error initializing components: {str(e)}")
    import traceback
    traceback.print_exc()
    # We'll initialize them as None and handle it in the endpoints
    document_indexer = None
    query_engine = None


class QueryRequest(BaseModel):
    query: str
    folder_id: Optional[str] = None


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
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ],
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
async def auth_callback(request: Request):
    """Handle OAuth callback from frontend"""
    body = await request.json()
    code = body.get("code")
    state = body.get("state")

        # Verify state to prevent CSRF
    if state not in auth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing required parameters (code or state)")
    
    # Clean up state
    del auth_states[state]
    
    # Create flow with same redirect URI
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ],
        redirect_uri="http://localhost:3000/auth/callback"  # Frontend URL
    )
    
    # Exchange authorization code for tokens
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials in session
        request.session["credentials"] = credentials.to_json()

        # Extract user info
        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Store user ID and email in session
        request.session["user_id"] = user_info["id"]
        request.session["email"] = user_info["email"]
        
        # Generate a session ID for the frontend
        session_id = secrets.token_urlsafe(32)
        request.session["session_id"] = session_id

        print(request.session.get("user_id"))
        print(request.session.get("email"))
        
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
        credentials_info = json.loads(credentials_json)
        credentials = Credentials.from_authorized_user_info(credentials_info)
        
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
async def process_folder(request: Request):
    """
    Process all files in a Google Drive folder and create an index.
    Uses the authenticated user's credentials.
    """
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        request_body = await request.json()

        if not request_body.folder_id:
            raise HTTPException(status_code=400, detail="folder_id is required")
        
        # Create a DocumentProcessor with the user's drive service
        user_document_processor = DocumentProcessor(drive_service=drive_service)
        
        # Get all files from the folder
        try:
            files = user_document_processor.get_files_from_drive(request_body.folder_id)
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
            index_id = document_indexer.create_index(documents, request_body.folder_id, user_id=session_id)
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

@app.post("/api/process-folder-new")
async def process_folder_new(request: Request):
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        request_body = await request.json()

        if not request_body.folder_id:
            raise HTTPException(status_code=400, detail="folder_id is required")
        
        # Create a DocumentProcessor with the user's drive service
        user_document_processor = DocumentProcessor(drive_service=drive_service)

        local_json_store = LocalJsonStore()
        local_store = local_json_store.load("db")
        user_id = request.session.get("user_id")
        if user_id not in local_store:
            raise HTTPException(status_code=404, detail="User not found")
        
        target_folder = None

        def find_folder(childrens, folder_id):
            for child in childrens:
                if child["type"] == "folder" and child["id"] == folder_id:
                    target_folder = child
                    return
                if "contents" in child:
                    find_folder(child["children"], folder_id)

        if request_body.folder_id == "root":
            target_folder = local_store[user_id]
        else:
            find_folder(local_store[user_id]["contents"], request_body.folder_id)

        if target_folder is None:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        return target_folder
            
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
                query_request.folder_id
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
        print(f"Session contents in check_auth: {dict(request.session)}")
        
        credentials_json = request.session.get("credentials")
        if not credentials_json:
            return {"authenticated": False, "reason": "No credentials in session"}
        
        # Try to parse credentials to verify they're valid
        credentials_info = json.loads(credentials_json)
        credentials = Credentials.from_authorized_user_info(credentials_info)
        
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

# TESTING
@app.get("/api/drive/folder-structure")
async def get_folder_structure(request: Request, folder_id: Optional[str] = "root"):
    """
    Retrieve the folder structure from the user's Google Drive,
    starting from the specified folder (or root by default).
    
    Parameters:
    - folder_id: Optional ID of the folder to start traversal from (defaults to root)
    
    Returns a nested structure of folders.
    """
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        # Function to recursively get folders
        def get_folder_contents(folder_id, depth=0, max_depth=10):
            if depth > max_depth:  # Prevent excessive recursion
                return {"truncated": True, "reason": "Max depth reached"}
                
            # Get all folders in the current folder
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            folders = []
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
                
                folders.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                
                if not page_token:
                    break
            
            # Process and organize the results
            result = []
            for folder in folders:
                result.append({
                    "id": folder["id"],
                    "name": folder["name"],
                    "mimeType": folder["mimeType"],
                    "children": get_folder_contents(folder["id"], depth + 1, max_depth)  # Recursively get subfolders
                })
            return result
        
        # Get the folder structure starting from the specified folder_id
        folder_structure = get_folder_contents(folder_id)
        return folder_structure
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drive/file-structure")
async def get_file_structure(request: Request, folder_id: Optional[str] = "root"):
    """
    Retrieve the complete file structure with metadata from the user's Google Drive,
    starting from the specified folder (or root by default).
    
    Parameters:
    - folder_id: Optional ID of the folder to start traversal from (defaults to root)
    
    Returns a nested structure of folders and files with their metadata.
    """
    try:
        # Get the authenticated user's drive service
        drive_service = await get_drive_service(request)
        
        # Function to recursively get files and folders
        def get_folder_contents(folder_id, depth=0, max_depth=10):
            if depth > max_depth:  # Prevent excessive recursion
                return {"truncated": True, "reason": "Max depth reached"}
                
            # Get all files and folders in the current folder
            query = f"'{folder_id}' in parents and trashed=false"
            
            items = []
            page_token = None
            
            while True:
                response = (
                    drive_service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink, owners, sharingUser, shared, capabilities)",
                        pageToken=page_token,
                    )
                    .execute()
                )
                
                items.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                
                if not page_token:
                    break
            
            # Process and organize the results
            result = []
            for item in items:
                mimeType = item.get("mimeType")
                
                item_data = {
                    "id": item["id"],
                    "name": item["name"],
                    "mimeType": item["mimeType"],
                    "createdTime": item.get("createdTime"),
                    "modifiedTime": item.get("modifiedTime"),
                    "size": item.get("size"),
                    "webViewLink": item.get("webViewLink"),
                    "shared": item.get("shared", False),
                    "permissions": {
                        "canEdit": item.get("capabilities", {}).get("canEdit", False),
                        "canComment": item.get("capabilities", {}).get("canComment", False),
                        "canCopy": item.get("capabilities", {}).get("canCopy", False),
                    }
                }
                
                # Add owner information if available
                if "owners" in item and item["owners"]:
                    owner = item["owners"][0]  # Get the primary owner
                    item_data["owner"] = {
                        "displayName": owner.get("displayName"),
                        "emailAddress": owner.get("emailAddress")
                    }
                
                # For folders, recursively get their contents
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    item_data["type"] = "folder"
                    # Only recurse if we haven't reached max depth
                    if depth < max_depth:
                        item_data["children"] = get_folder_contents(item["id"], depth + 1, max_depth)
                else:
                    item_data["type"] = "file"
                
                result.append(item_data)
            
            return result
        
        # Start the recursive file structure retrieval
        file_structure = get_folder_contents(folder_id)
        
        # Get folder details for the starting folder (if not root)
        folder_details = None
        if folder_id != "root":
            folder_details = drive_service.files().get(
                fileId=folder_id, 
                fields="id, name, mimeType, createdTime, modifiedTime"
            ).execute()
        

        obj = {
            "folder_id": folder_id,
            "folder_details": folder_details,
            "contents": file_structure
        }
        
        
        try:
            user_id = request.session.get("user_id")
            local_json_store = LocalJsonStore()
            local_store = local_json_store.load("db")
            if user_id not in local_store:
                local_store[user_id] = {}
            
            local_json_store.deep_merge(local_store[user_id], obj)
            local_json_store.save("db", local_store)
        except Exception as e:
            print(f"Error while saving to local JSON store: {str(e)}")

        return obj
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error retrieving file structure: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file structure: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)