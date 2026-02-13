"""Pet management endpoints."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.storage import get_storage_service
from db.session import get_db
from dependencies import get_current_active_user, get_current_user_id, get_pet_service
from exceptions import PetNotFoundException, PermissionDeniedException
from models.pet_photo import PetPhoto
from models.user import User
from schemas.common import ApiResponse, MessageResponse
from schemas.pet import Pet, PetCreate, PetPublic, PetUpdate
from services.pet_service import PetService
from utils.filters import PetFilter
from utils.pagination import PaginatedResponse, PaginationParams, paginate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedResponse[PetPublic]],
    summary="Search pets",
    description="Advanced search for pets with multiple filters and text search"
)
async def search_pets(
    q: Optional[str] = Query(None, description="Search query for name, breed, or description"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    city_id: Optional[int] = Query(None, description="Filter by city ID"),
    status: Optional[str] = Query(None, description="Filter by status (available, adopted, lost, found, help)"),
    gender: Optional[str] = Query(None, description="Filter by gender (male, female)"),
    min_age: Optional[int] = Query(None, ge=0, description="Minimum age in months"),
    max_age: Optional[int] = Query(None, ge=0, description="Maximum age in months"),
    vaccinated: Optional[bool] = Query(None, description="Filter by vaccination status"),
    spayed: Optional[bool] = Query(None, description="Filter by spayed/neutered status"),
    pagination: PaginationParams = Depends(),
    pet_service: PetService = Depends(get_pet_service)
):
    """Search pets with advanced filtering."""
    filters = {
        "search_term": q,
        "category_id": category_id,
        "city_id": city_id,
        "status": status,
        "gender": gender,
        "min_age": min_age,
        "max_age": max_age,
        "vaccinated": vaccinated,
        "spayed": spayed
    }
    
    logger.info(f"Searching pets with filters: {filters}")
    
    pets, total = await pet_service.advanced_search(
        filters=filters,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    paginated = paginate(pets, total, pagination.page, pagination.page_size)
    
    return ApiResponse(
        success=True,
        data=paginated,
        message=f"Found {total} pets matching your search"
    )


@router.post(
    "/",
    response_model=ApiResponse[Pet],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pet",
    description="Create a new pet listing with optional photo uploads"
)
async def create_pet(
    name: str = Form(...),
    age: int = Form(...),
    category_id: int = Form(..., gt=0),
    city_id: int = Form(..., gt=0),
    description: str = Form(...),
    breed: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    status: Optional[str] = Form("available"),
    vaccinated: Optional[bool] = Form(None),
    spayed: Optional[bool] = Form(None),
    photos: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_active_user),
    pet_service: PetService = Depends(get_pet_service)
):
    """Create a new pet listing with optional photo uploads."""
    logger.info(f"Creating pet for user {current_user.id}")
    
    pet_data = {
        "name": name,
        "age": age,
        "category_id": category_id,
        "city_id": city_id,
        "description": description,
        "breed": breed,
        "gender": gender,
        "status": status,
        "vaccinated": vaccinated,
        "spayed": spayed,
        "owner_id": current_user.id
    }
    
    # Upload photos if provided
    uploaded_photo_urls = []
    if photos:
        storage = get_storage_service()
        
        for photo in photos[:5]:  # Max 5 photos
            try:
                photo.file.seek(0, 2)
                photo.file.seek(0)
                
                url = await storage.upload_file(
                    file=photo.file,
                    filename=photo.filename,
                    content_type=photo.content_type,
                    folder="pets"
                )
                
                uploaded_photo_urls.append(url)
                logger.info(f"Uploaded photo: {url}")
            except Exception as e:
                logger.error(f"Failed to upload photo {photo.filename}: {e}")
                continue
    
    # Set main photo if available
    if uploaded_photo_urls:
        pet_data["main_photo_url"] = uploaded_photo_urls[0]
    
    pet = await pet_service.create(pet_data)
    
    # Create PetPhoto records for uploaded photos
    if uploaded_photo_urls:
        async for db in get_db():
            for photo_url in uploaded_photo_urls:
                pet_photo = PetPhoto(
                    pet_id=pet.id,
                    url=photo_url
                )
                db.add(pet_photo)
            
            await db.commit()
            break
        
        # Re-fetch pet with photos
        pet = await pet_service.get_pet_with_details(pet.id)
    
    return ApiResponse(success=True, data=pet, message="Pet created successfully")


@router.post(
    "/json",
    response_model=ApiResponse[Pet],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pet (JSON)",
    description="Create a new pet listing from a JSON body (no photo uploads)"
)
async def create_pet_json(
    pet_in: PetCreate,
    current_user: User = Depends(get_current_active_user),
    pet_service: PetService = Depends(get_pet_service)
):
    """Create a new pet listing from JSON. Photos can be uploaded separately."""
    logger.info(f"Creating pet (JSON) for user {current_user.id}")

    pet_data = pet_in.model_dump()
    pet_data["owner_id"] = current_user.id

    pet = await pet_service.create(pet_data)

    return ApiResponse(success=True, data=pet, message="Pet created successfully")


@router.get(
    "/",
    response_model=ApiResponse[PaginatedResponse[PetPublic]],
    summary="List all pets",
    description="Get a paginated list of available pets with optional filters"
)
async def list_pets(
    pagination: PaginationParams = Depends(),
    filters: PetFilter = Depends(),
    pet_service: PetService = Depends(get_pet_service)
):
    """Get all available pets with filters and pagination."""
    logger.info(f"Listing pets with filters: {filters.model_dump()}")
    
    pets = await pet_service.search_available_pets(
        skip=pagination.skip,
        limit=pagination.limit,
        city_id=filters.city_id,
        category_id=filters.category_id,
        search_term=filters.search
    )
    
    total = await pet_service.count(filters.to_dict())
    paginated = paginate(pets, total, pagination.page, pagination.page_size)
    
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/my-pets",
    response_model=ApiResponse[List[Pet]],
    summary="Get my pets",
    description="Get all pets belonging to the current user"
)
async def list_my_pets(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    pet_service: PetService = Depends(get_pet_service)
):
    """Get current user's pets."""
    logger.info(f"Listing pets for user {current_user.id}")
    
    pets = await pet_service.get_user_pets(
        owner_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return ApiResponse(success=True, data=pets)


@router.get(
    "/{pet_id}",
    response_model=ApiResponse[Pet],
    summary="Get pet by ID",
    description="Get detailed information about a specific pet"
)
async def get_pet(
    pet_id: UUID,
    pet_service: PetService = Depends(get_pet_service)
):
    """Get pet by ID with full details."""
    logger.info(f"Getting pet {pet_id}")
    
    pet = await pet_service.get_pet_with_details(pet_id)
    
    if not pet:
        raise PetNotFoundException()
    
    return ApiResponse(success=True, data=pet)


@router.patch(
    "/{pet_id}",
    response_model=ApiResponse[Pet],
    summary="Update a pet",
    description="Update pet information (owner only)"
)
async def update_pet(
    pet_id: UUID,
    pet_update: PetUpdate,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service),
    db: AsyncSession = Depends(get_db)
):
    """Update a pet listing."""
    logger.info(f"Updating pet {pet_id}")
    
    # Verify ownership
    if not await pet_service.verify_owner(pet_id, current_user_id):
        raise PermissionDeniedException("update this pet")
    
    update_data = pet_update.model_dump(exclude_unset=True)
    pet = await pet_service.update(pet_id, update_data)
    
    if not pet:
        raise PetNotFoundException()
    
    return ApiResponse(success=True, data=pet, message="Pet updated successfully")


@router.delete(
    "/{pet_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a pet",
    description="Soft delete a pet listing (owner only)"
)
async def delete_pet(
    pet_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service)
):
    """Soft delete a pet listing."""
    logger.info(f"Deleting pet {pet_id}")
    
    # Verify ownership
    if not await pet_service.verify_owner(pet_id, current_user_id):
        raise PermissionDeniedException("delete this pet")
    
    pet = await pet_service.soft_delete(pet_id)
    
    if not pet:
        raise PetNotFoundException()
    
    return MessageResponse(success=True, message="Pet deleted successfully")


@router.post(
    "/{pet_id}/publish",
    response_model=ApiResponse[Pet],
    summary="Publish a pet",
    description="Make a pet listing public"
)
async def publish_pet(
    pet_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service)
):
    """Make a pet listing public."""
    logger.info(f"Publishing pet {pet_id}")
    
    pet = await pet_service.publish_pet(pet_id, current_user_id)
    
    if not pet:
        raise PermissionDeniedException("publish this pet")
    
    return ApiResponse(success=True, data=pet, message="Pet published successfully")


@router.post(
    "/{pet_id}/unpublish",
    response_model=ApiResponse[Pet],
    summary="Unpublish a pet",
    description="Make a pet listing private"
)
async def unpublish_pet(
    pet_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    pet_service: PetService = Depends(get_pet_service)
):
    """Make a pet listing private."""
    logger.info(f"Unpublishing pet {pet_id}")
    
    pet = await pet_service.unpublish_pet(pet_id, current_user_id)
    
    if not pet:
        raise PermissionDeniedException("unpublish this pet")
    
    return ApiResponse(success=True, data=pet, message="Pet unpublished successfully")
