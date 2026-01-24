"""Storage service for file uploads - Cloudflare R2 implementation."""
import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from core.config import settings

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract storage service interface."""
    
    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = ""
    ) -> str:
        """Upload file and return public URL."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_url: str) -> bool:
        """Delete file by URL."""
        pass


class CloudflareR2Storage(StorageService):
    """Cloudflare R2 storage implementation."""
    
    def __init__(self):
        """Initialize R2 client."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
        logger.info(f"Cloudflare R2 storage initialized with bucket: {self.bucket}")
    
    def _generate_unique_filename(self, original_filename: str, folder: str = "") -> str:
        """Generate unique filename with UUID."""
        extension = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{extension}"
        
        if folder:
            return f"{folder}/{unique_name}"
        return unique_name
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = ""
    ) -> str:
        """
        Upload file to Cloudflare R2.
        
        Args:
            file: File object to upload
            filename: Original filename
            content_type: MIME type of file
            folder: Optional folder path (e.g., 'pets', 'missing-animals')
        
        Returns:
            Public URL of uploaded file
        """
        try:
            # Generate unique filename
            object_key = self._generate_unique_filename(filename, folder)
            
            # Upload to R2
            self.client.upload_fileobj(
                file,
                self.bucket,
                object_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'CacheControl': 'public, max-age=31536000',  # 1 year cache
                }
            )
            
            # Generate public URL
            public_url = f"{self.public_url}/{object_key}"
            
            logger.info(f"File uploaded successfully: {object_key}")
            return public_url
            
        except ClientError as e:
            logger.error(f"Error uploading file to R2: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete file from R2 by URL.
        
        Args:
            file_url: Full public URL of the file
        
        Returns:
            True if deleted successfully
        """
        try:
            # Extract object key from URL
            object_key = file_url.replace(f"{self.public_url}/", "")
            
            # Delete from R2
            self.client.delete_object(
                Bucket=self.bucket,
                Key=object_key
            )
            
            logger.info(f"File deleted successfully: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from R2: {e}")
            return False
    
    def get_file_url(self, object_key: str) -> str:
        """Get public URL for an object key."""
        return f"{self.public_url}/{object_key}"


class LocalStorage(StorageService):
    """Local filesystem storage (for development)."""
    
    def __init__(self):
        """Initialize local storage."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = settings.LOCAL_STORAGE_URL
        logger.info(f"Local storage initialized at: {self.upload_dir}")
    
    def _generate_unique_filename(self, original_filename: str, folder: str = "") -> str:
        """Generate unique filename with UUID."""
        extension = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{extension}"
        
        if folder:
            return f"{folder}/{unique_name}"
        return unique_name
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        folder: str = ""
    ) -> str:
        """Upload file to local filesystem."""
        try:
            # Generate unique filename
            relative_path = self._generate_unique_filename(filename, folder)
            file_path = self.upload_dir / relative_path
            
            # Create folder if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            with open(file_path, "wb") as f:
                file.seek(0)
                f.write(file.read())
            
            # Generate public URL
            public_url = f"{self.base_url}/{relative_path}"
            
            logger.info(f"File uploaded locally: {relative_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading file locally: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from local filesystem."""
        try:
            # Extract relative path from URL
            relative_path = file_url.replace(f"{self.base_url}/", "")
            file_path = self.upload_dir / relative_path
            
            # Delete file
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted locally: {relative_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting local file: {e}")
            return False


# Factory function to get storage service
def get_storage_service() -> StorageService:
    """
    Get storage service based on configuration.
    
    Returns:
        StorageService instance (R2 or Local)
    """
    if settings.STORAGE_PROVIDER == "r2":
        return CloudflareR2Storage()
    elif settings.STORAGE_PROVIDER == "local":
        return LocalStorage()
    else:
        raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")
