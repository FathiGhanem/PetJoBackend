"""Schemas for file uploads."""
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    url: str = Field(..., description="Public URL of uploaded file")
    filename: str = Field(..., description="Generated filename")
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://pub-xyz.r2.dev/pets/abc123.jpg",
                "filename": "abc123.jpg",
                "content_type": "image/jpeg",
                "size": 1024000
            }
        }


class MultipleFileUploadResponse(BaseModel):
    """Response for multiple file uploads."""
    files: list[FileUploadResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "url": "https://pub-xyz.r2.dev/pets/abc123.jpg",
                        "filename": "abc123.jpg",
                        "content_type": "image/jpeg",
                        "size": 1024000
                    }
                ],
                "total": 1
            }
        }
