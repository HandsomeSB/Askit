# document_processor.py
import os
from typing import List, Dict, Any, BinaryIO
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload

# Import various file type processors
from llama_index.readers.file import PDFReader, DocxReader
from llama_index.readers.file.tabular import PandasExcelReader
from llama_index.readers.file.image import ImageReader
from llama_index.core import Document


# This class with process the files and return a list that looks like this:
# all_documents = [
#     # From Google Presentation
#     Document(
#         text="Slide 1 content...",
#         metadata={
#             "file_name": "presentation.pptx",
#             "file_id": "456def",
#             "mime_type": "application/vnd.google-apps.presentation",
#         },
#     ),
#     Document(
#         text="Slide 2 content...",
#         metadata={
#             "file_name": "presentation.pptx",
#             "file_id": "456def",
#             "mime_type": "application/vnd.google-apps.presentation",
#         },
#     ),
#     # If there were any errors processing a file
#     Document(
#         text="Error processing file: [error message]",
#         metadata={
#             "file_name": "problematic_file.xyz",
#             "file_id": "789ghi",
#             "mime_type": "unknown/type",
#             "error": "Error message details",
#         },
#     ),
#     # ... more documents from other files
# ]


class DocumentProcessor:
    """
    Process files from Google Drive and convert to LlamaIndex documents.
    Handles various file types including PDF, DOCX, images, Excel, etc.
    """

    # Google Workspace MIME types
    GOOGLE_DOC_MIMETYPES = {
        "application/vnd.google-apps.document": {
            "export_type": "text/plain",
            "processor": "_process_text",
        },
        "application/vnd.google-apps.spreadsheet": {
            "export_type": "text/csv",
            "processor": "_process_text",
        },
        "application/vnd.google-apps.presentation": {
            "export_type": "text/plain",
            "processor": "_process_text",
        },
    }

    def __init__(self):
        """Initialize document processor with file type handlers"""
        self.pdf_reader = PDFReader()
        self.docx_reader = DocxReader()
        self.excel_reader = PandasExcelReader()
        self.image_reader = ImageReader()

        # Set up Google Drive connection
        self.drive_service = self._setup_drive_connection()

    def _setup_drive_connection(self):
        """
        Set up connection to Google Drive using OAuth2.

        Returns:
            Google Drive service object
        """

        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = None

        # Check if credentials.json exists
        if not os.path.exists("credentials.json"):
            print(
                "ERROR: credentials.json file not found. Please set up Google Drive API credentials."
            )
            raise FileNotFoundError(
                "credentials.json file not found. Please set up Google Drive API credentials."
            )

        # Load credentials from token.json if available
        if os.path.exists("token.json"):
            try:
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
                print("Loaded credentials from token.json")
            except Exception as e:
                print(f"Error loading credentials from token.json: {str(e)}")
                # If token.json is corrupted, we'll create a new one

        # If no valid credentials, authenticate user
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("Refreshed expired credentials")
                except Exception as e:
                    print(f"Error refreshing credentials: {str(e)}")
                    # If refresh fails, we'll create new credentials
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", SCOPES
                    )
                    print("Starting OAuth flow for Google Drive authentication")
                    creds = flow.run_local_server(port=0)
                    print("Successfully authenticated with Google Drive")
                except Exception as e:
                    print(f"Error during OAuth flow: {str(e)}")
                    raise Exception(
                        f"Failed to authenticate with Google Drive: {str(e)}"
                    )

            # Save credentials for next run
            try:
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                print("Saved credentials to token.json")
            except Exception as e:
                print(f"Error saving credentials to token.json: {str(e)}")

        # Build Drive service
        try:
            service = build("drive", "v3", credentials=creds)
            print("Successfully built Google Drive service")
            return service
        except Exception as e:
            print(f"Error building Google Drive service: {str(e)}")
            raise Exception(f"Failed to build Google Drive service: {str(e)}")

    # This function is scanning all the files in a folder and returning a list of dictonaries each representing a file metadata
    def get_files_from_drive(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Get all files from a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            List of file metadata dictionaries
        """
        files = []
        page_token = None

        # Query files within the specified folder
        query = f"'{folder_id}' in parents and trashed=false"

        while True:
            response = (
                self.drive_service.files()
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

        return files

    # This function is using the file metadata received from the previous function and using the `file_id` to download the file and return a list of documents
    def process_file(self, file_metadata: Dict[str, Any]) -> List[Document]:
        """
        Process a file from Google Drive based on its mime type.

        Args:
            file_metadata: File metadata from Google Drive

        Returns:
            List of LlamaIndex Document objects
        """
        file_id = file_metadata["id"]
        file_name = file_metadata["name"]
        mime_type = file_metadata["mimeType"]

        print(f"Processing file: {file_name} (ID: {file_id}, Type: {mime_type})")

        # Handle Google Workspace files
        if mime_type in self.GOOGLE_DOC_MIMETYPES:
            try:
                print(f"Exporting Google Workspace file: {file_name}")
                file_content = self._export_google_file(file_id, mime_type)
                processor = getattr(
                    self, self.GOOGLE_DOC_MIMETYPES[mime_type]["processor"]
                )
                return processor(file_content, file_metadata)
            except Exception as e:
                print(f"Error processing Google Workspace file {file_name}: {str(e)}")
                # Return a document with error information
                return [
                    Document(
                        text=f"Error processing Google Workspace file: {str(e)}",
                        metadata={
                            "file_name": file_name,
                            "file_id": file_id,
                            "mime_type": mime_type,
                            "error": str(e),
                        },
                    )
                ]

        # Handle other file types
        try:
            file_content = self._download_file(file_id)
        except Exception as e:
            print(f"Error downloading file {file_name}: {str(e)}")
            # Return a document with error information
            return [
                Document(
                    text=f"Error downloading file: {str(e)}",
                    metadata={
                        "file_name": file_name,
                        "file_id": file_id,
                        "mime_type": mime_type,
                        "error": str(e),
                    },
                )
            ]

        # Process based on file type
        try:
            if mime_type == "application/pdf":
                return self._process_pdf(file_content, file_metadata)
            elif (
                mime_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return self._process_docx(file_content, file_metadata)
            elif (
                mime_type
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ):
                return self._process_excel(file_content, file_metadata)
            elif mime_type.startswith("image/"):
                return self._process_image(file_content, file_metadata)
            elif (
                mime_type.startswith("audio/")
                or mime_type == "application/octet-stream"
            ):
                return self._process_audio(file_content, file_metadata)
            else:
                # Default processing for unknown types - convert to string if possible
                return self._process_text(file_content, file_metadata)
        except Exception as e:
            print(f"Error processing file {file_name}: {str(e)}")
            # Return a document with error information
            return [
                Document(
                    text=f"Error processing file: {str(e)}",
                    metadata={
                        "file_name": file_name,
                        "file_id": file_id,
                        "mime_type": mime_type,
                        "error": str(e),
                    },
                )
            ]

    def _export_google_file(self, file_id: str, mime_type: str) -> BinaryIO:
        """
        Export a Google Workspace file in the specified format.

        Args:
            file_id: Google Drive file ID
            mime_type: Original mime type of the file

        Returns:
            File content as bytes-like object
        """
        export_mime_type = self.GOOGLE_DOC_MIMETYPES[mime_type]["export_type"]

        # Create a BytesIO object to store the downloaded content
        file_content = io.BytesIO()

        # Use the export_media method with the correct parameters
        request = self.drive_service.files().export_media(
            fileId=file_id, mimeType=export_mime_type
        )

        # Use MediaIoBaseDownload to handle the download properly
        downloader = MediaIoBaseDownload(file_content, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}% complete")

        # Reset the file pointer to the beginning
        file_content.seek(0)
        return file_content

    def _download_file(self, file_id: str) -> BinaryIO:
        """
        Download file content from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as bytes-like object
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()

        # Use MediaIoBaseDownload to handle the download properly
        downloader = MediaIoBaseDownload(file_content, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}% complete")

        # Reset the file pointer to the beginning
        file_content.seek(0)
        return file_content

    def _process_pdf(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process PDF file"""
        documents = self.pdf_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(
                {
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                }
            )
        return documents

    def _process_docx(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process DOCX file"""
        documents = self.docx_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(
                {
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                }
            )
        return documents

    def _process_excel(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process Excel file"""
        documents = self.excel_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(
                {
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                }
            )
        return documents

    def _process_image(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process image file with OCR and image understanding"""
        documents = self.image_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(
                {
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                }
            )
        return documents

    def _process_audio(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process audio file - currently returns metadata only"""
        doc = Document(
            text="[Audio file content not processed]",
            metadata={
                "file_name": file_metadata["name"],
                "file_id": file_metadata["id"],
                "mime_type": file_metadata["mimeType"],
                "note": "Audio transcription not available in current version",
            },
        )
        return [doc]

    def _process_text(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process text file"""
        try:
            # Try to read content as text
            content = file_content.read().decode("utf-8")
            doc = Document(
                text=content,
                metadata={
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                },
            )
            return [doc]
        except UnicodeDecodeError:
            # If can't decode as text, create a document with just metadata
            doc = Document(
                text=f"Binary file: {file_metadata['name']}",
                metadata={
                    "file_name": file_metadata["name"],
                    "file_id": file_metadata["id"],
                    "mime_type": file_metadata["mimeType"],
                    "content_type": "binary",
                },
            )
            return [doc]
