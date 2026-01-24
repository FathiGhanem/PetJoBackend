"""Pet help request endpoints."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from core.storage import get_storage_service
from dependencies import get_current_active_user, get_current_user_id, get_pet_help_service
from exceptions import PermissionDeniedException
from models.user import User
from schemas.common import ApiResponse, MessageResponse
from schemas.pet_help import (
    PetHelpRequest,
    PetHelpRequestCreate,
    PetHelpRequestPublic,
    PetHelpRequestUpdate,
)
from services.pet_help_service import PetHelpRequestService
from utils.pagination import PaginatedResponse, PaginationParams, paginate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[PetHelpRequest],
    status_code=status.HTTP_201_CREATED,
    summary="Create help request",
    description="Create a new pet help request with optional photos"
)
async def create_help_request(
    title: str = Form(...),
    description: str = Form(...),
    city_id: int = Form(...),
    location: str = Form(...),
    contact_phone: str = Form(...),
    contact_email: Optional[str] = Form(None),
    urgency_level: Optional[str] = Form("medium"),
    animal_type: Optional[str] = Form(None),
    photos: Optional[List[UploadFile]] = File(None, description="Photos of the animal (max 3)"),
    current_user: User = Depends(get_current_active_user),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Create a new pet help request with optional photo uploads."""
    logger.info(f"Creating help request for user {current_user.id}")
    
    # Upload photos if provided
    photo_url = None
    if photos:
        storage = get_storage_service()
        
        for photo in photos[:3]:  # Max 3 photos
            try:
                photo.file.seek(0, 2)
                photo.file.seek(0)
                
                url = await storage.upload_file(
                    file=photo.file,
                    filename=photo.filename,
                    content_type=photo.content_type,
                    folder="help-requests"
                )
                
                if not photo_url:
                    photo_url = url  # Use first photo
                
                logger.info(f"Uploaded help request photo: {url}")
            except Exception as e:
                logger.error(f"Failed to upload photo {photo.filename}: {e}")
                continue
    
    # Create help request data
    help_data = {
        "title": title,
        "description": description,
        "city_id": city_id,
        "location": location,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "urgency_level": urgency_level,
        "animal_type": animal_type,
        "owner_id": current_user.id,
        "photo_url": photo_url
    }
    
    help_request = await help_service.create(help_data)
    
    return ApiResponse(
        success=True,
        data=help_request,
        message="Help request created successfully"
    )


@router.get(
    "/",
    response_model=ApiResponse[PaginatedResponse[PetHelpRequestPublic]],
    summary="List all help requests",
    description="Get a paginated list of all pet help requests"
)
async def list_help_requests(
    pagination: PaginationParams = Depends(),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Get all help requests with pagination."""
    logger.info(f"Listing help requests (page {pagination.page})")
    
    help_requests = await help_service.get_all_public_requests(
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    total = await help_service.count({})
    paginated = paginate(help_requests, total, pagination.page, pagination.page_size)
    
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/search",
    response_model=ApiResponse[List[PetHelpRequestPublic]],
    summary="Search help requests by location",
    description="Search for help requests within a radius of a location"
)
async def search_help_requests_by_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(10.0, ge=0.1, le=100, description="Search radius in kilometers"),
    pagination: PaginationParams = Depends(),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Search help requests by location."""
    logger.info(f"Searching help requests near ({lat}, {lng}) within {radius}km")
    
    help_requests = await help_service.search_by_location(
        lat=lat,
        lng=lng,
        radius_km=radius,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return ApiResponse(
        success=True,
        data=help_requests,
        message=f"Found {len(help_requests)} help requests"
    )


@router.get(
    "/my-requests",
    response_model=ApiResponse[List[PetHelpRequest]],
    summary="Get my help requests",
    description="Get all help requests created by the current user"
)
async def list_my_help_requests(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Get current user's help requests."""
    logger.info(f"Listing help requests for user {current_user.id}")
    
    help_requests = await help_service.get_user_help_requests(
        owner_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return ApiResponse(success=True, data=help_requests)


@router.get(
    "/{help_id}",
    response_model=ApiResponse[PetHelpRequest],
    summary="Get help request by ID",
    description="Get detailed information about a specific help request"
)
async def get_help_request(
    help_id: int,
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Get help request by ID with full details."""
    logger.info(f"Getting help request {help_id}")
    
    help_request = await help_service.get_help_request_with_details(help_id)
    
    if not help_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found"
        )
    
    return ApiResponse(success=True, data=help_request)


@router.patch(
    "/{help_id}",
    response_model=ApiResponse[PetHelpRequest],
    summary="Update help request",
    description="Update help request information (owner only)"
)
async def update_help_request(
    help_id: int,
    help_update: PetHelpRequestUpdate,
    current_user_id: str = Depends(get_current_user_id),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Update a help request."""
    logger.info(f"Updating help request {help_id}")
    
    # Verify ownership
    if not await help_service.verify_owner(help_id, UUID(current_user_id)):
        raise PermissionDeniedException("update this help request")
    
    update_data = help_update.model_dump(exclude_unset=True)
    help_request = await help_service.update(help_id, update_data)
    
    if not help_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found"
        )
    
    return ApiResponse(
        success=True,
        data=help_request,
        message="Help request updated successfully"
    )


@router.delete(
    "/{help_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete help request",
    description="Delete a help request (owner only)"
)
async def delete_help_request(
    help_id: int,
    current_user_id: str = Depends(get_current_user_id),
    help_service: PetHelpRequestService = Depends(get_pet_help_service)
):
    """Delete a help request."""
    logger.info(f"Deleting help request {help_id}")
    
    # Verify ownership
    if not await help_service.verify_owner(help_id, UUID(current_user_id)):
        raise PermissionDeniedException("delete this help request")
    
    success = await help_service.delete(help_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help request not found"
        )
    
    return MessageResponse(success=True, message="Help request deleted successfully")
