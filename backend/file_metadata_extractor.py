import os
from typing import Dict, Any, Optional
import mimetypes
from datetime import datetime
import magic
import mutagen
from PIL import Image
import exifread
import ffmpeg
import json
import re
from PIL import ExifTags


class FileMetadataExtractor:
    """Handles metadata extraction for various file types"""

    # Common metadata fields for all files
    COMMON_METADATA = [
        "file_name",
        "file_id",
        "mime_type",
        "created_time",
        "modified_time",
        "size",
        "web_view_link",
        "thumbnail_link",
        "file_extension",
        "file_type_category",  # e.g., 'image', 'video', 'audio', 'document', 'code'
    ]

    @staticmethod
    def get_file_type_category(mime_type: str) -> str:
        """Determine the general category of a file based on its MIME type"""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("text/"):
            return "text"
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            return "document"
        elif mime_type in [
            "application/json",
            "application/xml",
            "text/x-python",
            "text/javascript",
        ]:
            return "code"
        else:
            return "other"

    @staticmethod
    def extract_image_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from image files"""
        metadata = {}
        try:
            with Image.open(file_path) as img:
                # Basic image metadata
                metadata.update(
                    {
                        "width": img.width,
                        "height": img.height,
                        "format": img.format,
                        "mode": img.mode,
                        "is_animated": getattr(img, "is_animated", False),
                        "n_frames": getattr(img, "n_frames", 1),
                    }
                )

                # Extract EXIF data using PIL for HEIC files
                if img.format in ["HEIC", "HEIF"]:
                    exif = img.getexif()
                    if exif:
                        # Convert EXIF data to a more readable format
                        exif_data = {}
                        for tag_id in exif:
                            # Get the tag name
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            value = exif.get(tag_id)
                            # Decode bytes values if necessary
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode()
                                except UnicodeDecodeError:
                                    value = str(value)
                            exif_data[tag] = str(value)

                        metadata["exif"] = exif_data

                        # Extract common EXIF fields
                        if "DateTime" in exif_data:
                            metadata["capture_time"] = exif_data["DateTime"]
                        if "Make" in exif_data:
                            metadata["camera_make"] = exif_data["Make"]
                        if "Model" in exif_data:
                            metadata["camera_model"] = exif_data["Model"]
                else:
                    # Use exifread for non-HEIC images as it's more comprehensive
                    with open(file_path, "rb") as f:
                        tags = exifread.process_file(f)
                        if tags:
                            metadata["exif"] = {
                                str(tag): str(value) for tag, value in tags.items()
                            }

                            # Extract common EXIF fields
                            if "EXIF DateTimeOriginal" in tags:
                                metadata["capture_time"] = str(
                                    tags["EXIF DateTimeOriginal"]
                                )
                            if "Image Make" in tags:
                                metadata["camera_make"] = str(tags["Image Make"])
                            if "Image Model" in tags:
                                metadata["camera_model"] = str(tags["Image Model"])
                            if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                                metadata["location"] = {
                                    "latitude": str(tags["GPS GPSLatitude"]),
                                    "longitude": str(tags["GPS GPSLongitude"]),
                                }

        except Exception as e:
            print(f"Error extracting image metadata: {str(e)}")
        return metadata

    @staticmethod
    def extract_video_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from video files"""
        metadata = {}
        try:
            probe = ffmpeg.probe(file_path)
            if probe and "streams" in probe:
                video_stream = next(
                    (
                        stream
                        for stream in probe["streams"]
                        if stream["codec_type"] == "video"
                    ),
                    None,
                )
                audio_stream = next(
                    (
                        stream
                        for stream in probe["streams"]
                        if stream["codec_type"] == "audio"
                    ),
                    None,
                )

                if video_stream:
                    metadata.update(
                        {
                            "video_codec": video_stream.get("codec_name"),
                            "width": video_stream.get("width"),
                            "height": video_stream.get("height"),
                            "duration": video_stream.get("duration"),
                            "fps": video_stream.get("r_frame_rate"),
                            "bitrate": video_stream.get("bit_rate"),
                        }
                    )

                if audio_stream:
                    metadata.update(
                        {
                            "audio_codec": audio_stream.get("codec_name"),
                            "sample_rate": audio_stream.get("sample_rate"),
                            "channels": audio_stream.get("channels"),
                            "audio_bitrate": audio_stream.get("bit_rate"),
                        }
                    )

                if "format" in probe:
                    metadata.update(
                        {
                            "container_format": probe["format"].get("format_name"),
                            "file_size": probe["format"].get("size"),
                            "duration": probe["format"].get("duration"),
                            "bitrate": probe["format"].get("bit_rate"),
                        }
                    )
        except Exception as e:
            print(f"Error extracting video metadata: {str(e)}")
        return metadata

    @staticmethod
    def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from audio files"""
        metadata = {}
        try:
            audio = mutagen.File(file_path)
            if audio:
                metadata.update(
                    {
                        "duration": (
                            audio.info.length if hasattr(audio, "info") else None
                        ),
                        "bitrate": (
                            audio.info.bitrate if hasattr(audio, "info") else None
                        ),
                        "sample_rate": (
                            audio.info.sample_rate if hasattr(audio, "info") else None
                        ),
                        "channels": (
                            audio.info.channels if hasattr(audio, "info") else None
                        ),
                    }
                )

                # Extract ID3 tags if available
                if hasattr(audio, "tags"):
                    metadata["tags"] = {
                        str(tag): str(value) for tag, value in audio.tags.items()
                    }
        except Exception as e:
            print(f"Error extracting audio metadata: {str(e)}")
        return metadata

    @staticmethod
    def extract_text_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from text files"""
        metadata = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                metadata.update(
                    {
                        "line_count": len(content.splitlines()),
                        "word_count": len(content.split()),
                        "character_count": len(content),
                    }
                )

                # Detect programming language for code files
                if file_path.endswith(
                    (".py", ".js", ".java", ".cpp", ".c", ".h", ".html", ".css")
                ):
                    metadata["language"] = os.path.splitext(file_path)[1][1:]
        except Exception as e:
            print(f"Error extracting text metadata: {str(e)}")
        return metadata

    @staticmethod
    def extract_document_metadata(file_path: str) -> Dict[str, Any]:
        """Extract metadata from document files (PDF, DOCX, etc.)"""
        metadata = {}
        try:
            # Use magic to detect file type
            file_type = magic.from_file(file_path, mime=True)

            if file_type == "application/pdf":
                # PDF specific metadata
                metadata.update(
                    {
                        "page_count": None,  # Would need PyPDF2 or similar to get this
                        "author": None,
                        "title": None,
                        "subject": None,
                    }
                )
            elif file_type in [
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]:
                # Word document specific metadata
                metadata.update(
                    {
                        "page_count": None,  # Would need python-docx to get this
                        "author": None,
                        "title": None,
                        "subject": None,
                    }
                )
        except Exception as e:
            print(f"Error extracting document metadata: {str(e)}")
        return metadata

    @staticmethod
    def extract_metadata(file_path: str, mime_type: str) -> Dict[str, Any]:
        """Main method to extract metadata based on file type"""
        metadata = {}
        file_type_category = FileMetadataExtractor.get_file_type_category(mime_type)

        # Add common metadata
        metadata["file_type_category"] = file_type_category

        # Extract type-specific metadata
        if file_type_category == "image":
            metadata.update(FileMetadataExtractor.extract_image_metadata(file_path))
        elif file_type_category == "video":
            metadata.update(FileMetadataExtractor.extract_video_metadata(file_path))
        elif file_type_category == "audio":
            metadata.update(FileMetadataExtractor.extract_audio_metadata(file_path))
        elif file_type_category == "text":
            metadata.update(FileMetadataExtractor.extract_text_metadata(file_path))
        elif file_type_category == "document":
            metadata.update(FileMetadataExtractor.extract_document_metadata(file_path))

        return metadata
