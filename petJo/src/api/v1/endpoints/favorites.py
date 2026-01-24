"""Favorites endpoints."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_active_user, get_favorite_service
from models.user import User
from schemas.common import ApiResponse, MessageResponse
from schemas.favorite import Favorite, FavoriteCreate, FavoriteWithPet
from services.favorite_service import FavoriteService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ApiResponse[List[FavoriteWithPet]],
    summary="Get my favorites",
    description="Get all favorite pets for the current user"
)
async def get_my_favorites(
    current_user: User = Depends(get_current_active_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Get current user's favorite pets."""
    logger.info(f"Getting favorites for user {current_user.id}")
    
    favorites = await favorite_service.get_user_favorites(current_user.id)
    
    return ApiResponse(
        success=True,
        data=favorites,
        message=f"Retrieved {len(favorites)} favorites"
    )


@router.post(
    "/",
    response_model=ApiResponse[Favorite],
    status_code=status.HTTP_201_CREATED,
    summary="Add to favorites",
    description="Add a pet to favorites"
)
async def add_favorite(
    favorite_in: FavoriteCreate,
    current_user: User = Depends(get_current_active_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Add pet to favorites."""
    logger.info(f"User {current_user.id} adding pet {favorite_in.pet_id} to favorites")
    
    favorite = await favorite_service.add_favorite(current_user.id, favorite_in.pet_id)
    
    return ApiResponse(
        success=True,
        data=favorite,
        message="Pet added to favorites"
    )


@router.delete(
    "/{pet_id}",
    response_model=MessageResponse,
    summary="Remove from favorites",
    description="Remove a pet from favorites"
)
async def remove_favorite(
    pet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Remove pet from favorites."""
    logger.info(f"User {current_user.id} removing pet {pet_id} from favorites")
    
    success = await favorite_service.remove_favorite(current_user.id, pet_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    return MessageResponse(
        success=True,
        message="Pet removed from favorites"
    )


@router.get(
    "/check/{pet_id}",
    response_model=ApiResponse[dict],
    summary="Check if favorited",
    description="Check if a pet is in user's favorites"
)
async def check_favorite(
    pet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Check if pet is favorited."""
    logger.info(f"Checking if user {current_user.id} favorited pet {pet_id}")
    
    is_favorited = await favorite_service.is_favorited(current_user.id, pet_id)
    
    return ApiResponse(
        success=True,
        data={"is_favorited": is_favorited, "pet_id": str(pet_id)}
    )
