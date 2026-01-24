"""File upload endpoints."""
import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from core.config import settings
from core.storage import get_storage_service
from dependencies import get_current_user
from models.user import User
from schemas.common import ApiResponse
from schemas.upload import FileUploadResponse, MultipleFileUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed image types
# Allowed image types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic"
}

# Allowed extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def validate_image(file: UploadFile) -> None:
    """
    Validate uploaded image file.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If validation fails
    """
    from pathlib import Path
    
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_mb}MB"
        )
    
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )


async def _upload_single_file(
    file: UploadFile,
    folder: str,
    user_email: str
) -> FileUploadResponse:
    """
    Helper function to upload a single file.
    
    Args:
        file: File to upload
        folder: Destination folder
        user_email: User email for logging
        
    Returns:
        FileUploadResponse with upload details
        
    Raises:
        HTTPException: If upload fails
    """
    validate_image(file)
    
    # Get file size before upload
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    storage = get_storage_service()
    
    try:
        url = await storage.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=file.content_type,
            folder=folder
        )
        
        return FileUploadResponse(
            url=url,
            filename=file.filename,
            content_type=file.content_type,
            size=file_size
        )
        
    except Exception as e:
        logger.error(f"Upload failed for {user_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.post(
    "/pet-photo",
    response_model=ApiResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload pet photo",
    description="Upload a photo for a pet listing. Returns the public URL."
)
async def upload_pet_photo(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP, HEIC)"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a pet photo.
    
    - **Allowed formats**: JPEG, PNG, WebP, HEIC
    - **Max size**: Configured in settings (default 10MB)
    - **Authentication**: Required
    """
    logger.info(f"User {current_user.email} uploading pet photo: {file.filename}")
    
    data = await _upload_single_file(file, "pets", current_user.email)
    
    return ApiResponse(
        success=True,
        data=data,
        message="Photo uploaded successfully"
    )


@router.post(
    "/missing-animal-photo",
    response_model=ApiResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload missing animal photo"
)
async def upload_missing_animal_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload photo for missing animal report."""
    logger.info(f"User {current_user.email} uploading missing animal photo")
    
    data = await _upload_single_file(file, "missing-animals", current_user.email)
    
    return ApiResponse(
        success=True,
        data=data,
        message="Photo uploaded successfully"
    )


@router.post(
    "/help-request-photo",
    response_model=ApiResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload pet help request photo"
)
async def upload_help_request_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload photo for pet help request."""
    logger.info(f"User {current_user.email} uploading help request photo")
    
    data = await _upload_single_file(file, "help-requests", current_user.email)
    
    return ApiResponse(
        success=True,
        data=data,
        message="Photo uploaded successfully"
    )


@router.post(
    "/multiple",
    response_model=ApiResponse[MultipleFileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple photos",
    description="Upload multiple photos at once (max 10 files)"
)
async def upload_multiple_photos(
    files: List[UploadFile] = File(..., description="Multiple image files"),
    folder: str = "general",
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple photos at once.
    
    - **Max files**: 10 per request
    - **Allowed formats**: JPEG, PNG, WebP, HEIC
    - **Max size per file**: Configured in settings
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per upload"
        )
    
    logger.info(f"User {current_user.email} uploading {len(files)} photos")
    
    storage = get_storage_service()
    uploaded_files = []
    
    for file in files:
        try:
            validate_image(file)
            
            # Get file size before upload
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            
            url = await storage.upload_file(
                file=file.file,
                filename=file.filename,
                content_type=file.content_type,
                folder=folder
            )
            
            uploaded_files.append(FileUploadResponse(
                url=url,
                filename=file.filename,
                content_type=file.content_type,
                size=file_size
            ))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed for {file.filename}: {e}")
            # Continue with other files
            continue
    
    return ApiResponse(
        success=True,
        data=MultipleFileUploadResponse(
            files=uploaded_files,
            total=len(uploaded_files)
        ),
        message=f"Uploaded {len(uploaded_files)} photos successfully"
    )
