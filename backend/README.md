# AsKit - Google Drive Document Processing and Querying

This backend system allows users to authenticate with Google Drive, process documents from their Drive, and ask questions about those documents using semantic search and LLM-based answering.

## Features

- Google OAuth authentication
- Secure session management
- Process and index files from Google Drive
  - Support for PDFs, Word documents, Excel spreadsheets, images, and more
  - Extracts metadata and text content
- Vector-based semantic search
- Natural language querying with metadata filtering
- Persistence of indices for fast repeated access

## Requirements

- Python 3.9+
- Google Cloud Platform account with Drive API enabled
- OpenAI API key for embeddings and LLM

## Project Structure

- `app.py` - FastAPI application with route handlers
- `document_processor.py` - Processes files from Google Drive
- `indexer.py` - Creates and manages vector indices
- `query_engine.py` - Handles natural language queries
- `file_metadata_extractor.py` - Extracts metadata from files
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (API keys, etc.)

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up Google Drive API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials.json file and place it in the project root
6. Create a `.env` file with the following:
   ```
   OPENAI_API_KEY=your_openai_key
   SESSION_SECRET_KEY=your_random_secret_key
   ```
7. Run the application: `./start.sh` or `python -m uvicorn app:main --reload`

## API Endpoints

### Authentication

- `GET /api/auth/google-url` - Get Google OAuth URL
- `POST /api/auth/google-callback` - Handle OAuth callback
- `GET /api/auth/check` - Check authentication status
- `POST /api/auth/logout` - Log out user

### Google Drive

- `GET /api/folders` - List all folders
- `GET /api/drive/folder-structure` - Get folder hierarchy
- `GET /api/drive/file-structure` - Get files and folders with metadata

### Document Processing

- `POST /api/process-folder` - Process all files in a Google Drive folder
  ```json
  {
    "folder_id": "google_drive_folder_id"
  }
  ```

### Querying

- `POST /api/query` - Query indexed documents
  ```json
  {
    "query": "your natural language query",
    "folder_id": "google_drive_folder_id"
  }
  ```

## Usage Example

```python
import requests

# Authentication
auth_url = requests.get('http://localhost:8000/api/auth/google-url').json()['url']
print(f"Visit this URL to authenticate: {auth_url}")

# After authentication and redirection, get the code from the URL
code = "..." # From redirect URL
auth_response = requests.post('http://localhost:8000/api/auth/google-callback', json={'code': code, 'state': '...'})
session_id = auth_response.json()['session_id']

# Set session cookie for subsequent requests
cookies = {'session': session_id}

# List folders
folders = requests.get('http://localhost:8000/api/folders', cookies=cookies).json()

# Process a folder
folder_id = "..." # Select a folder ID from the list
process_response = requests.post(
    'http://localhost:8000/api/process-folder',
    json={'folder_id': folder_id},
    cookies=cookies
).json()

# Query the indexed documents
query_response = requests.post(
    'http://localhost:8000/api/query',
    json={'query': 'What are the main points about quantum computing?', 'folder_id': folder_id},
    cookies=cookies
).json()

print(f"Answer: {query_response['answer']}")
print(f"Sources: {len(query_response['sources'])}")
```

## Enhanced Features

- **Metadata Filtering**: Query using natural language filters like "documents from last month" or "images about cats"
- **Document Chunking**: Smart splitting of documents for better context retrieval
- **Hybrid Search**: Combines semantic search with metadata filtering
- **Session Management**: Secure handling of user sessions and authentication

## Troubleshooting

- If you get authentication errors, check your `credentials.json` file and ensure the Google API is enabled
- For document processing errors, check the logs for specific file errors
- Make sure your `.env` file contains valid API keys
