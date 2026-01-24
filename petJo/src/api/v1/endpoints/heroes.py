"""Public hero section endpoints."""
import logging
from typing import List

from fastapi import APIRouter, Depends

from dependencies import get_hero_service
from schemas.common import ApiResponse
from schemas.hero import Hero as HeroSchema
from services.hero_service import HeroService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ApiResponse[List[HeroSchema]],
    summary="Get all hero items",
    description="Retrieve all hero section items for display"
)
async def get_all_heroes(
    skip: int = 0,
    limit: int = 100,
    hero_service: HeroService = Depends(get_hero_service)
):
    """Get all hero items (public endpoint)."""
    logger.info("Fetching all hero items")
    
    heroes = await hero_service.get_all_heroes(skip, limit)
    
    return ApiResponse(
        success=True,
        data=heroes,
        message=f"Retrieved {len(heroes)} hero items"
    )
