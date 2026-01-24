"""Public endpoints for categories and cities."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.advertisement import Advertisement
from models.category import Category
from models.city import City
from models.pet import Pet, PetStatus
from models.pet_help_request import PetHelpRequest
from models.user import User
from schemas.category import Category as CategorySchema
from schemas.city import City as CitySchema
from schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Statistics Endpoint ====================


@router.get(
    "/stats",
    summary="Get public statistics",
    description="Get public statistics about the platform"
)
async def get_public_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get public statistics."""
    logger.info("Fetching public statistics")
    
    # Get counts
    total_pets = await db.scalar(
        select(func.count()).select_from(Pet).where(Pet.deleted_at.is_(None))
    )
    available_pets = await db.scalar(
        select(func.count()).select_from(Pet).where(
            Pet.deleted_at.is_(None),
            Pet.status == PetStatus.AVAILABLE
        )
    )
    adopted_pets = await db.scalar(
        select(func.count()).select_from(Pet).where(
            Pet.deleted_at.is_(None),
            Pet.status == PetStatus.ADOPTED
        )
    )
    help_requests = await db.scalar(
        select(func.count()).select_from(PetHelpRequest)
    )
    categories = await db.scalar(
        select(func.count()).select_from(Category)
    )
    cities = await db.scalar(
        select(func.count()).select_from(City)
    )
    
    return ApiResponse(
        success=True,
        data={
            "pets": {
                "total": total_pets,
                "available": available_pets,
                "adopted": adopted_pets
            },
            "help_requests": help_requests,
            "categories": categories,
            "cities": cities
        },
        message="Public statistics retrieved"
    )


# ==================== Category Endpoints ====================


@router.get(
    "/categories",
    response_model=ApiResponse[List[CategorySchema]],
    summary="Get all categories",
    description="Retrieve all pet categories"
)
async def get_all_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all categories (public endpoint)."""
    logger.info("Fetching all categories")
    
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=list(categories),
        message=f"Retrieved {len(categories)} categories"
    )


@router.get(
    "/categories/{category_id}",
    response_model=ApiResponse[CategorySchema],
    summary="Get category by ID",
    description="Get a specific category by ID"
)
async def get_category_by_id(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get category by ID (public endpoint)."""
    logger.info(f"Fetching category {category_id}")
    
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return ApiResponse(
        success=True,
        data=category
    )


# ==================== City Endpoints ====================


@router.get(
    "/cities",
    response_model=ApiResponse[List[CitySchema]],
    summary="Get all cities",
    description="Retrieve all cities"
)
async def get_all_cities(
    db: AsyncSession = Depends(get_db)
):
    """Get all cities (public endpoint)."""
    logger.info("Fetching all cities")
    
    result = await db.execute(select(City))
    cities = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=list(cities),
        message=f"Retrieved {len(cities)} cities"
    )


@router.get(
    "/cities/{city_id}",
    response_model=ApiResponse[CitySchema],
    summary="Get city by ID",
    description="Get a specific city by ID"
)
async def get_city_by_id(
    city_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get city by ID (public endpoint)."""
    logger.info(f"Fetching city {city_id}")
    
    result = await db.execute(
        select(City).where(City.id == city_id)
    )
    city = result.scalar_one_or_none()
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found"
        )
    
    return ApiResponse(
        success=True,
        data=city
    )
