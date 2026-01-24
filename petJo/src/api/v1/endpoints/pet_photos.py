"""Pet photos endpoints."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_user_id, get_pet_photo_service, get_pet_service
from schemas.common import ApiResponse, MessageResponse
from schemas.pet_photo import PetPhoto, PetPhotoCreate
from services.pet_photo_service import PetPhotoService
from services.pet_service import PetService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{pet_id}/photos",
    response_model=ApiResponse[List[PetPhoto]],
    summary="Get pet photos",
    description="Get all photos for a specific pet"
)
async def get_pet_photos(
    pet_id: UUID,
    pet_photo_service: PetPhotoService = Depends(get_pet_photo_service)
):
    """Get all photos for a pet."""
    logger.info(f"Getting photos for pet {pet_id}")
    
    photos = await pet_photo_service.get_pet_photos(pet_id)
    
    return ApiResponse(
        success=True,
        data=photos,
        message=f"Retrieved {len(photos)} photos"
    )


@router.post(
    "/{pet_id}/photos",
    response_model=ApiResponse[PetPhoto],
    status_code=status.HTTP_201_CREATED,
    summary="Add pet photo",
    description="Add a photo to a pet (owner only)"
)
async def add_pet_photo(
    pet_id: UUID,
    photo_in: PetPhotoCreate,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service),
    pet_photo_service: PetPhotoService = Depends(get_pet_photo_service)
):
    """Add photo to pet."""
    logger.info(f"Adding photo to pet {pet_id}")
    
    # Verify ownership
    if not await pet_service.verify_owner(pet_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add photos to this pet"
        )
    
    photo_data = photo_in.model_dump()
    photo_data["pet_id"] = pet_id
    
    photo = await pet_photo_service.create(photo_data)
    
    return ApiResponse(
        success=True,
        data=photo,
        message="Photo added successfully"
    )


@router.delete(
    "/{pet_id}/photos/{photo_id}",
    response_model=MessageResponse,
    summary="Delete pet photo",
    description="Delete a pet photo (owner only)"
)
async def delete_pet_photo(
    pet_id: UUID,
    photo_id: int,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service),
    pet_photo_service: PetPhotoService = Depends(get_pet_photo_service)
):
    """Delete pet photo."""
    logger.info(f"Deleting photo {photo_id} from pet {pet_id}")
    
    # Verify ownership
    if not await pet_service.verify_owner(pet_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete photos from this pet"
        )
    
    success = await pet_photo_service.delete(photo_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    return MessageResponse(
        success=True,
        message="Photo deleted successfully"
    )
