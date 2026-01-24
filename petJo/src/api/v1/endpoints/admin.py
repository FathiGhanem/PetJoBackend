"""Admin-only endpoints for system management."""
import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from dependencies import get_current_superuser, get_hero_service, get_user_service
from exceptions import UserNotFoundException
from models.advertisement import Advertisement
from models.category import Category
from models.city import City
from models.pet import Pet, PetStatus
from models.user import User
from schemas.category import Category as CategorySchema
from schemas.category import CategoryCreate, CategoryUpdate
from schemas.city import City as CitySchema
from schemas.city import CityCreate, CityUpdate
from schemas.common import ApiResponse, MessageResponse
from schemas.hero import Hero as HeroSchema
from schemas.hero import HeroCreate, HeroUpdate
from schemas.pet import Pet as PetSchema
from schemas.user import User as UserSchema
from services.hero_service import HeroService
from services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/users",
    response_model=ApiResponse[List[UserSchema]],
    summary="Get all users (Admin only)",
    description="Retrieve all users in the system. Requires super admin access."
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get all users. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all users")
    
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=users,
        message=f"Retrieved {len(users)} users"
    )


@router.get(
    "/stats",
    summary="Get system statistics (Admin only)",
    description="Get overall system statistics. Requires super admin access."
)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get system statistics. Admin only."""
    logger.info(f"Admin {current_user.email} fetching system stats")
    
    # Get user counts
    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(
        select(func.count()).select_from(User).where(User.is_active == True)
    )
    
    # Get pet counts
    total_pets = await db.scalar(select(func.count()).select_from(Pet).where(Pet.deleted_at.is_(None)))
    available_pets = await db.scalar(
        select(func.count()).select_from(Pet).where(
            and_(Pet.status == PetStatus.AVAILABLE.value, Pet.deleted_at.is_(None))
        )
    )
    adopted_pets = await db.scalar(
        select(func.count()).select_from(Pet).where(
            and_(Pet.status == PetStatus.ADOPTED.value, Pet.deleted_at.is_(None))
        )
    )
    
    # Get category and city counts
    total_categories = await db.scalar(select(func.count()).select_from(Category))
    total_cities = await db.scalar(select(func.count()).select_from(City))
    
    # Get advertisement counts
    total_ads = await db.scalar(select(func.count()).select_from(Advertisement))
    pending_ads = await db.scalar(
        select(func.count()).select_from(Advertisement).where(Advertisement.status == "pending")
    )
    approved_ads = await db.scalar(
        select(func.count()).select_from(Advertisement).where(Advertisement.status == "approved")
    )
    rejected_ads = await db.scalar(
        select(func.count()).select_from(Advertisement).where(Advertisement.status == "rejected")
    )
    
    stats = {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
        "pets": {
            "total": total_pets,
            "available": available_pets,
            "adopted": adopted_pets,
        },
        "advertisements": {
            "total": total_ads,
            "pending": pending_ads,
            "approved": approved_ads,
            "rejected": rejected_ads,
        },
        "categories": total_categories,
        "cities": total_cities,
    }
    
    return ApiResponse(
        success=True,
        data=stats,
        message="System statistics retrieved"
    )


@router.patch(
    "/users/{user_id}/activate",
    response_model=ApiResponse[UserSchema],
    summary="Activate user (Admin only)",
    description="Activate a user account. Requires super admin access."
)
async def activate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Activate a user. Admin only."""
    from uuid import UUID
    
    logger.info(f"Admin {current_user.email} activating user {user_id}")
    
    user = await user_service.activate_user(UUID(user_id))
    
    if not user:
        raise UserNotFoundException()
    
    return ApiResponse(
        success=True,
        data=user,
        message="User activated successfully"
    )


@router.patch(
    "/users/{user_id}/deactivate",
    response_model=ApiResponse[UserSchema],
    summary="Deactivate user (Admin only)",
    description="Deactivate a user account. Requires super admin access."
)
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Deactivate a user. Admin only."""
    from uuid import UUID
    
    logger.info(f"Admin {current_user.email} deactivating user {user_id}")
    
    user = await user_service.deactivate_user(UUID(user_id))
    
    if not user:
        raise UserNotFoundException()
    
    return ApiResponse(
        success=True,
        data=user,
        message="User deactivated successfully"
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (Admin only)",
    description="Permanently delete a user account. Requires super admin access."
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete a user. Admin only."""
    from uuid import UUID
    
    logger.warning(f"Admin {current_user.email} deleting user {user_id}")
    
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundException()
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        from exceptions import ValidationException
        raise ValidationException("Cannot delete your own account")
    
    # Prevent deleting other superusers
    if user.is_superuser:
        from exceptions import ValidationException
        raise ValidationException("Cannot delete other superuser accounts")
    
    await db.delete(user)
    await db.commit()
    
    return None


# ===================== PET MANAGEMENT =====================

@router.get(
    "/pets",
    response_model=ApiResponse[List[PetSchema]],
    summary="Get all pets (Admin only)",
    description="Retrieve all pets including deleted ones. Requires super admin access."
)
async def get_all_pets(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get all pets. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all pets")
    
    query = select(Pet)
    
    if not include_deleted:
        query = query.where(Pet.deleted_at.is_(None))
    
    if status:
        query = query.where(Pet.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Pet.created_at.desc())
    
    result = await db.execute(query)
    pets = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=pets,
        message=f"Retrieved {len(pets)} pets"
    )


@router.patch(
    "/pets/{pet_id}/status",
    response_model=ApiResponse[PetSchema],
    summary="Update pet status (Admin only)",
    description="Update pet status. Requires super admin access."
)
async def update_pet_status(
    pet_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update pet status. Admin only."""
    logger.info(f"Admin {current_user.email} updating pet {pet_id} status to {status}")
    
    # Validate status
    try:
        PetStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join([s.value for s in PetStatus])}"
        )
    
    result = await db.execute(
        select(Pet).where(Pet.id == UUID(pet_id))
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    pet.status = status
    pet.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(pet)
    
    return ApiResponse(
        success=True,
        data=pet,
        message=f"Pet status updated to {status}"
    )


@router.delete(
    "/pets/{pet_id}",
    response_model=ApiResponse[dict],
    summary="Delete pet (Admin only)",
    description="Soft delete a pet. Requires super admin access."
)
async def delete_pet_admin(
    pet_id: str,
    permanent: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete pet. Admin only."""
    logger.warning(f"Admin {current_user.email} deleting pet {pet_id} (permanent={permanent})")
    
    result = await db.execute(
        select(Pet).where(Pet.id == UUID(pet_id))
    )
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    if permanent:
        await db.delete(pet)
        message = "Pet permanently deleted"
    else:
        pet.deleted_at = datetime.utcnow()
        message = "Pet soft deleted"
    
    await db.commit()
    
    return ApiResponse(
        success=True,
        data={"pet_id": str(pet_id), "permanent": permanent},
        message=message
    )


# ===================== CATEGORY MANAGEMENT =====================

@router.get(
    "/categories",
    response_model=ApiResponse[List[CategorySchema]],
    summary="Get all categories (Admin only)",
    description="Retrieve all categories. Requires super admin access."
)
async def get_all_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get all categories. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all categories")
    
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=categories,
        message=f"Retrieved {len(categories)} categories"
    )


@router.post(
    "/categories",
    response_model=ApiResponse[CategorySchema],
    status_code=status.HTTP_201_CREATED,
    summary="Create category (Admin only)",
    description="Create a new category. Requires super admin access."
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create category. Admin only."""
    logger.info(f"Admin {current_user.email} creating category: {category_data.name}")
    
    # Check if category already exists
    result = await db.execute(
        select(Category).where(Category.name == category_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    category = Category(**category_data.dict())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return ApiResponse(
        success=True,
        data=category,
        message="Category created successfully"
    )


@router.patch(
    "/categories/{category_id}",
    response_model=ApiResponse[CategorySchema],
    summary="Update category (Admin only)",
    description="Update a category. Requires super admin access."
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update category. Admin only."""
    logger.info(f"Admin {current_user.email} updating category {category_id}")
    
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    
    return ApiResponse(
        success=True,
        data=category,
        message="Category updated successfully"
    )


@router.delete(
    "/categories/{category_id}",
    response_model=ApiResponse[dict],
    summary="Delete category (Admin only)",
    description="Delete a category. Requires super admin access."
)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete category. Admin only."""
    logger.warning(f"Admin {current_user.email} deleting category {category_id}")
    
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category is used by pets
    pets_count = await db.scalar(
        select(func.count()).select_from(Pet).where(Pet.category_id == category_id)
    )
    
    if pets_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category. It is used by {pets_count} pets"
        )
    
    await db.delete(category)
    await db.commit()
    
    return ApiResponse(
        success=True,
        data={"category_id": category_id},
        message="Category deleted successfully"
    )


# ===================== CITY MANAGEMENT =====================

@router.get(
    "/cities",
    response_model=ApiResponse[List[CitySchema]],
    summary="Get all cities (Admin only)",
    description="Retrieve all cities. Requires super admin access."
)
async def get_all_cities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get all cities. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all cities")
    
    result = await db.execute(select(City))
    cities = result.scalars().all()
    
    return ApiResponse(
        success=True,
        data=cities,
        message=f"Retrieved {len(cities)} cities"
    )


@router.post(
    "/cities",
    response_model=ApiResponse[CitySchema],
    status_code=status.HTTP_201_CREATED,
    summary="Create city (Admin only)",
    description="Create a new city. Requires super admin access."
)
async def create_city(
    city_data: CityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create city. Admin only."""
    logger.info(f"Admin {current_user.email} creating city: {city_data.name}")
    
    # Check if city already exists
    result = await db.execute(
        select(City).where(City.name == city_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City with this name already exists"
        )
    
    city = City(**city_data.dict())
    db.add(city)
    await db.commit()
    await db.refresh(city)
    
    return ApiResponse(
        success=True,
        data=city,
        message="City created successfully"
    )


@router.patch(
    "/cities/{city_id}",
    response_model=ApiResponse[CitySchema],
    summary="Update city (Admin only)",
    description="Update a city. Requires super admin access."
)
async def update_city(
    city_id: int,
    city_data: CityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Update city. Admin only."""
    logger.info(f"Admin {current_user.email} updating city {city_id}")
    
    result = await db.execute(
        select(City).where(City.id == city_id)
    )
    city = result.scalar_one_or_none()
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found"
        )
    
    # Update fields
    update_data = city_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(city, field, value)
    
    await db.commit()
    await db.refresh(city)
    
    return ApiResponse(
        success=True,
        data=city,
        message="City updated successfully"
    )


@router.delete(
    "/cities/{city_id}",
    response_model=ApiResponse[dict],
    summary="Delete city (Admin only)",
    description="Delete a city. Requires super admin access."
)
async def delete_city(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete city. Admin only."""
    logger.warning(f"Admin {current_user.email} deleting city {city_id}")
    
    result = await db.execute(
        select(City).where(City.id == city_id)
    )
    city = result.scalar_one_or_none()
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="City not found"
        )
    
    # Check if city is used by pets or users
    pets_count = await db.scalar(
        select(func.count()).select_from(Pet).where(Pet.city_id == city_id)
    )
    users_count = await db.scalar(
        select(func.count()).select_from(User).where(User.city == city_id)
    )
    
    if pets_count > 0 or users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete city. It is used by {pets_count} pets and {users_count} users"
        )
    
    await db.delete(city)
    await db.commit()
    
    return ApiResponse(
        success=True,
        data={"city_id": city_id},
        message="City deleted successfully"
    )


# ==================== Hero Section Endpoints ====================


@router.get(
    "/heroes",
    response_model=ApiResponse[List[HeroSchema]],
    summary="Get all hero items (Admin only)",
    description="Retrieve all hero section items. Requires super admin access."
)
async def get_all_heroes(
    skip: int = 0,
    limit: int = 100,
    hero_service: HeroService = Depends(get_hero_service),
    current_user: User = Depends(get_current_superuser)
):
    """Get all hero items. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all heroes")
    
    heroes = await hero_service.get_all_heroes(skip, limit)
    
    return ApiResponse(
        success=True,
        data=heroes,
        message=f"Retrieved {len(heroes)} hero items"
    )


@router.get(
    "/heroes/{hero_id}",
    response_model=ApiResponse[HeroSchema],
    summary="Get hero by ID (Admin only)",
    description="Get a specific hero item by ID. Requires super admin access."
)
async def get_hero_by_id(
    hero_id: int,
    hero_service: HeroService = Depends(get_hero_service),
    current_user: User = Depends(get_current_superuser)
):
    """Get hero by ID. Admin only."""
    logger.info(f"Admin {current_user.email} fetching hero {hero_id}")
    
    hero = await hero_service.get(hero_id)
    
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hero item not found"
        )
    
    return ApiResponse(
        success=True,
        data=hero
    )


@router.post(
    "/heroes",
    response_model=ApiResponse[HeroSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Create hero item (Admin only)",
    description="Create a new hero section item. Requires super admin access."
)
async def create_hero(
    hero_in: HeroCreate,
    hero_service: HeroService = Depends(get_hero_service),
    current_user: User = Depends(get_current_superuser)
):
    """Create new hero item. Admin only."""
    logger.info(f"Admin {current_user.email} creating hero item")
    
    hero_data = hero_in.model_dump()
    hero = await hero_service.create(hero_data)
    
    return ApiResponse(
        success=True,
        data=hero,
        message="Hero item created successfully"
    )


@router.patch(
    "/heroes/{hero_id}",
    response_model=ApiResponse[HeroSchema],
    summary="Update hero item (Admin only)",
    description="Update a hero section item. Requires super admin access."
)
async def update_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    hero_service: HeroService = Depends(get_hero_service),
    current_user: User = Depends(get_current_superuser)
):
    """Update hero item. Admin only."""
    logger.info(f"Admin {current_user.email} updating hero {hero_id}")
    
    hero = await hero_service.get(hero_id)
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hero item not found"
        )
    
    update_data = hero_update.model_dump(exclude_unset=True)
    updated_hero = await hero_service.update(hero_id, update_data)
    
    return ApiResponse(
        success=True,
        data=updated_hero,
        message="Hero item updated successfully"
    )


@router.delete(
    "/heroes/{hero_id}",
    response_model=MessageResponse,
    summary="Delete hero item (Admin only)",
    description="Delete a hero section item. Requires super admin access."
)
async def delete_hero(
    hero_id: int,
    hero_service: HeroService = Depends(get_hero_service),
    current_user: User = Depends(get_current_superuser)
):
    """Delete hero item. Admin only."""
    logger.warning(f"Admin {current_user.email} deleting hero {hero_id}")
    
    hero = await hero_service.get(hero_id)
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hero item not found"
        )
    
    success = await hero_service.delete(hero_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete hero item"
        )
    
    return MessageResponse(
        success=True,
        message="Hero item deleted successfully"
    )
