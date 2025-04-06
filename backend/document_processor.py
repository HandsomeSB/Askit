# document_processor.py
import os
from typing import List, Dict, Any, BinaryIO
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload
import tempfile
import pillow_heif
from PIL import Image

# Import various file type processors
from llama_index.readers.file import PDFReader, DocxReader
from llama_index.readers.file.tabular import PandasExcelReader
from llama_index.readers.file.image import ImageReader
from llama_index.core import Document

from file_metadata_extractor import FileMetadataExtractor


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

    # Register HEIF opener with Pillow
    pillow_heif.register_heif_opener()

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

        # Enhanced fields parameter to get more metadata
        fields = "nextPageToken,files(id,name,mimeType,createdTime,modifiedTime,imageMediaMetadata(time,cameraMake,cameraModel,location(latitude,longitude),width,height),thumbnailLink,webViewLink,size)"

        query = f"'{folder_id}' in parents and trashed=false"

        while True:
            response = (
                self.drive_service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields=fields,
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

        # Base metadata that all files will have
        base_metadata = {
            "file_name": file_name,
            "file_id": file_id,
            "mime_type": mime_type,
            "created_time": file_metadata.get("createdTime"),
            "modified_time": file_metadata.get("modifiedTime"),
            "web_view_link": file_metadata.get("webViewLink"),
            "thumbnail_link": file_metadata.get("thumbnailLink"),
            "size": file_metadata.get("size"),
        }

        try:
            # Handle Google Workspace files (Docs, Sheets, Slides)
            if mime_type in self.GOOGLE_DOC_MIMETYPES:
                export_type = self.GOOGLE_DOC_MIMETYPES[mime_type]["export_type"]
                request = self.drive_service.files().export_media(
                    fileId=file_id, mimeType=export_type
                )
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                content = fh.getvalue().decode("utf-8")
                return [Document(text=content, metadata=base_metadata)]

            # Handle regular files (PDF, DOCX, etc.)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                try:
                    # Download the file
                    request = self.drive_service.files().get_media(fileId=file_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()

                    temp_file.write(fh.getvalue())
                    temp_file_path = temp_file.name

                    # Extract additional metadata based on file type
                    additional_metadata = FileMetadataExtractor.extract_metadata(
                        temp_file_path, mime_type
                    )
                    base_metadata.update(additional_metadata)

                    # Process the file based on its type
                    if mime_type == "application/pdf":
                        try:
                            docs = self.pdf_reader.load_data(temp_file_path)
                            for doc in docs:
                                doc.metadata.update(base_metadata)
                            return docs
                        except Exception as pdf_error:
                            print(
                                f"Error processing PDF file {file_name}: {str(pdf_error)}"
                            )
                            return [
                                Document(
                                    text=f"Error processing PDF file: {str(pdf_error)}",
                                    metadata={**base_metadata, "error": str(pdf_error)},
                                )
                            ]
                    elif mime_type in [
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/msword",
                    ]:
                        try:
                            # Load the document first, then add metadata
                            docs = self.docx_reader.load_data(temp_file_path)
                            for doc in docs:
                                doc.metadata.update(base_metadata)
                            return docs
                        except Exception as docx_error:
                            print(
                                f"Error processing DOCX file {file_name}: {str(docx_error)}"
                            )
                            return [
                                Document(
                                    text=f"Error processing DOCX file: {str(docx_error)}",
                                    metadata={
                                        **base_metadata,
                                        "error": str(docx_error),
                                    },
                                )
                            ]
                    elif mime_type in [
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "application/vnd.ms-excel",
                    ]:
                        return self.excel_reader.load_data(
                            temp_file_path, metadata=base_metadata
                        )
                    elif mime_type.startswith("image/"):
                        try:
                            # Special handling for HEIC/HEIF images
                            if mime_type in ["image/heic", "image/heif"]:
                                # Open HEIC image
                                with Image.open(temp_file_path) as heic_img:
                                    # Create a temporary file for the converted JPEG
                                    with tempfile.NamedTemporaryFile(
                                        suffix=".jpg", delete=False
                                    ) as jpeg_temp:
                                        # Convert and save as JPEG
                                        heic_img.save(jpeg_temp.name, "JPEG")
                                        # Update the temp_file_path to point to the converted image
                                        temp_file_path = jpeg_temp.name

                            # Load the document first, then add metadata
                            docs = self.image_reader.load_data(temp_file_path)
                            for doc in docs:
                                doc.metadata.update(base_metadata)
                            return docs
                        except Exception as image_error:
                            print(
                                f"Error processing image file {file_name}: {str(image_error)}"
                            )
                            return [
                                Document(
                                    text=f"Error processing image file: {str(image_error)}",
                                    metadata={
                                        **base_metadata,
                                        "error": str(image_error),
                                    },
                                )
                            ]
                    else:
                        with open(temp_file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        return [Document(text=content, metadata=base_metadata)]

                finally:
                    # Clean up the temporary file
                    if "temp_file_path" in locals():
                        os.unlink(temp_file_path)

        except Exception as e:
            print(f"Error processing file {file_name}: {str(e)}")
            return [
                Document(
                    text=f"Error processing file: {str(e)}",
                    metadata={
                        **base_metadata,
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
            doc.metadata.update(file_metadata)
        return documents

    def _process_docx(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process DOCX file"""
        documents = self.docx_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(file_metadata)
        return documents

    def _process_excel(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process Excel file"""
        documents = self.excel_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(file_metadata)
        return documents

    def _process_image(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process image file with OCR and image understanding"""
        documents = self.image_reader.load_data(file_content)
        for doc in documents:
            doc.metadata.update(file_metadata)
        return documents

    def _process_audio(
        self, file_content: BinaryIO, file_metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process audio file - currently returns metadata only"""
        doc = Document(
            text="[Audio file content not processed]",
            metadata={
                "file_name": file_metadata["file_name"],
                "file_id": file_metadata["file_id"],
                "mime_type": file_metadata["mime_type"],
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
                metadata=file_metadata,
            )
            return [doc]
        except UnicodeDecodeError:
            # If can't decode as text, create a document with just metadata
            doc = Document(
                text=f"Binary file: {file_metadata['file_name']}",
                metadata={
                    "file_name": file_metadata["file_name"],
                    "file_id": file_metadata["file_id"],
                    "mime_type": file_metadata["mime_type"],
                    "content_type": "binary",
                },
            )
            return [doc]
