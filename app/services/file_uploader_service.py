import hashlib
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional, Set, Tuple

from flask import Request
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename

from app.libraries import logger
from config import CONFIG


@dataclass
class UploadConfig:
    """Configuration for file uploads."""
    allowed_extensions: Set[str] = frozenset({'pdf'})
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    max_pages: int = 5
    upload_dir: Path = CONFIG.DIRECTORIES.OUTPUT


class FileUploadError(Exception):
    """Custom exception for file upload errors."""
    pass


class FileUploader:
    def __init__(
            self,
            request: Request,
            config: Optional[UploadConfig] = None,
            file_field: str = 'cv'
    ):
        self.request = request
        self.config = config or UploadConfig()
        self.file_field = file_field
        self.uploaded_path: Optional[Path] = None

    def _is_allowed_file(self, filename: str) -> bool:
        """Check if the file extension is allowed."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.config.allowed_extensions

    @staticmethod
    def _is_allowed_mimetype(file) -> bool:
        """Verify file mimetype matches the extension."""
        try:
            mime_type = mimetypes.guess_type(file.filename)[0]
            return mime_type == 'application/pdf'
        except Exception:
            return False

    def _check_file_size(self, file) -> bool:
        """Verify file size is within limits."""
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Reset file pointer
        return size <= self.config.max_file_size

    @staticmethod
    def _generate_secure_filename(original_filename: str) -> str:
        """Generate a secure unique filename."""
        # Get secure base filename
        base_name = secure_filename(original_filename)

        # Add hash of original filename and timestamp for uniqueness
        timestamp = str(int(time.time()))
        name_hash = hashlib.md5(f"{base_name}{timestamp}".encode()).hexdigest()[:8]

        # Construct final filename
        filename, ext = os.path.splitext(base_name)
        return f"{filename}_{name_hash}{ext}"

    def _check_page_count(self, file) -> bool:
        try:
            # Create a temporary file to store the upload
            with NamedTemporaryFile(suffix='.pdf', delete=True) as temp_file:
                file.save(temp_file.name)
                file.seek(0)

                pdf = PdfReader(temp_file.name)
                page_count = len(pdf.pages)

                logger.info(f'PDF page count: {page_count}')
                return page_count <= self.config.max_pages

        except Exception as e:
            raise FileUploadError(f'Error reading PDF file: {str(e)}')

    def _ensure_upload_directory(self) -> None:
        """Ensure upload directory exists with proper permissions."""
        self.config.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file) -> None:
        """Validate uploaded file meets all requirements."""
        if not file or file.filename == '':
            raise FileUploadError('No file selected')

        if not self._is_allowed_file(file.filename):
            raise FileUploadError('File type not allowed')

        if not self._is_allowed_mimetype(file):
            raise FileUploadError('Invalid file type or corrupted file')

        if not self._check_file_size(file):
            raise FileUploadError(f'File size exceeds maximum limit of {self.config.max_file_size // 1024 // 1024}MB')

        if not self._check_page_count(file):
            raise FileUploadError(f'PDF exceeds maximum page limit of {self.config.max_pages} pages')

    def upload_file(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle file upload process with validation and security checks.

        Returns:
            tuple: (response_dict, status_code)
        """
        logger.info('Processing file upload request')

        try:
            # Check if file field exists in request
            if self.file_field not in self.request.files:
                raise FileUploadError('No file uploaded')

            self._ensure_upload_directory()

            file = self.request.files[self.file_field]

            self._validate_file(file)

            secure_name = self._generate_secure_filename(file.filename)
            self.uploaded_path = self.config.upload_dir / secure_name

            file.save(str(self.uploaded_path))

            logger.info(f'File successfully uploaded: {self.uploaded_path}')
            return {
                'message': 'File uploaded successfully',
                'path': str(self.uploaded_path)
            }, 200

        except FileUploadError as e:
            logger.warning(f'File upload validation error: {str(e)}')
            return {'error': str(e)}, 400

        except Exception as e:
            logger.exception(f'Unexpected error during file upload: {str(e)}')
            return {'error': 'Internal server error'}, 500

    def cleanup(self) -> None:
        """Clean up uploaded file in case of subsequent processing failure."""
        if not (self.uploaded_path and self.uploaded_path.exists()):
            return

        try:
            self.uploaded_path.unlink()
            logger.info(f'Cleaned up uploaded file: {self.uploaded_path}')
        except Exception as e:
            logger.error(f'Failed to cleanup file {self.uploaded_path}: {str(e)}')
