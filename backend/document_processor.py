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


    def __init__(self, drive_service=None):
        """Initialize document processor with file type handlers"""
        self.pdf_reader = PDFReader()
        self.docx_reader = DocxReader()
        self.excel_reader = PandasExcelReader()
        self.image_reader = ImageReader()

        # Use provided drive service or create a new one
        self.drive_service = drive_service
        
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

        if mime_type in self.GOOGLE_DOC_MIMETYPES:
            file_data = self._export_google_file(file_id, mime_type)
        else:
            file_data = self._download_file(file_id)
        try:
            # For Google Workspace files
            if mime_type in self.GOOGLE_DOC_MIMETYPES:
                processor_name = self.GOOGLE_DOC_MIMETYPES[mime_type]["processor"]
                processor_func = getattr(self, processor_name)
                return processor_func(file_data, base_metadata)

            # Check mime type and call appropriate processor
            if mime_type.startswith('application/pdf'):
                return self._process_pdf(file_data, base_metadata)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return self._process_docx(file_data, base_metadata)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                            'application/vnd.ms-excel']:
                return self._process_excel(file_data, base_metadata)
            elif mime_type.startswith('image/'):
                # Update metadata with image-specific info if available
                if 'imageMediaMetadata' in file_metadata:
                    img_meta = file_metadata['imageMediaMetadata'] or {}
                    base_metadata.update({
                        'capture_time': img_meta.get('time'),
                        'camera_make': img_meta.get('cameraMake'),
                        'camera_model': img_meta.get('cameraModel'),
                        'width': img_meta.get('width'),
                        'height': img_meta.get('height'),
                    })
                    if 'location' in img_meta and img_meta['location']:
                        base_metadata.update({
                            'latitude': img_meta['location'].get('latitude'),
                            'longitude': img_meta['location'].get('longitude'),
                        })
                return self._process_image(file_data, base_metadata)
            elif mime_type.startswith('audio/'):
                return self._process_audio(file_data, base_metadata)
            else:
                # For other file types, do not process
                # Return an empty list for unsupported file types
                print(f"Unsupported file type: {mime_type} for file: {file_name}")
                return [Document(
                    text=f"[Unsupported file type: {mime_type}]",
                    metadata=base_metadata
                )]
        except Exception as e:
            print(f"Error processing file {file_name}, {mime_type}: {e}")
            return [Document(
                text=f"[Error processing file: {file_name}]",
                metadata=base_metadata
            )]

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
        Download non-google work space file content from Google Drive.

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
