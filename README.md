# Askit - Semantic Search for Google Drive

## Overview

Askit is a powerful document search system that enables semantic search across your Google Drive documents. Unlike traditional keyword search, Askit understands the meaning behind your questions, delivering contextually relevant results from your documents.

## Features

- **Google Drive Integration**: Securely connect to your Google Drive account
- **Folder Processing**: Select and process specific folders for search indexing
- **Semantic Search**: Ask questions in natural language and get intelligent answers
- **Document Context**: View relevant document snippets that support search results
- **Search History**: Track and revisit previous searches
- **Modern UI**: Clean, responsive interface with visual feedback for processed folders
- **Data Persistence**: Remember processed folders between sessions

## Architecture

Askit consists of two main components:

### Backend (FastAPI)

- **Authentication**: Google OAuth 2.0 integration for secure access
- **Document Processing**: Extracts and processes text from various document formats
- **Indexing**: Creates semantic indexes of document content
- **Query Engine**: Processes natural language queries and retrieves relevant content

### Frontend (Next.js)

- **Modern React Components**: Built with Next.js and Tailwind CSS
- **Responsive Design**: Works on desktop and mobile devices
- **Intuitive Interface**: Folder selection, search bar, and results display
- **Session Management**: Handles authentication state and token refresh

## Setup Instructions

### Prerequisites

- Node.js (v16+)
- Python (v3.8+)
- Google Cloud Platform account with Drive API enabled

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   - Create a `.env` file in the backend directory
   - Add the following variables:
     ```
     SESSION_SECRET_KEY=your_secret_key
     GOOGLE_CLIENT_ID=your_google_client_id
     GOOGLE_CLIENT_SECRET=your_google_client_secret
     ```

5. Place your Google OAuth credentials file (`credentials.json`) in the backend directory

6. Start the backend server:
   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up environment variables:

   - Create a `.env.local` file in the frontend directory
   - Add the following:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```

4. Start the development server:

   ```bash
   npm run dev
   ```

5. Access the application at [http://localhost:3000](http://localhost:3000)

## Usage

1. **Sign In**: Log in with your Google account
2. **Select Folders**: Browse and select the Google Drive folders you want to search
3. **Process Folders**: Click "Process" on selected folders to index their contents
4. **Search Documents**: Enter natural language queries to search your documents
5. **Review Results**: View document snippets and click through to original files

## Development

### Adding New Features

The project is structured to make adding new features straightforward:

- Backend endpoints are defined in `app.py`
- Frontend components are in `src/components/`
- Services for API interactions are in `src/services/`

### Testing

Run the test suite with:

```bash
cd frontend
npm run test
```
