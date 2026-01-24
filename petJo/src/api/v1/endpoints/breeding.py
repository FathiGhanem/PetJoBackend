"""Breeding request endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from dependencies import get_current_active_user, get_breeding_request_service
from exceptions import NotFoundException, PermissionDeniedException
from models.user import User
from schemas.common import ApiResponse, MessageResponse
from schemas.breeding_request import (
    BreedingRequest,
    BreedingRequestCreate,
    BreedingRequestPublic,
    BreedingRequestStatusUpdate,
    BreedingRequestUpdate
)
from services.breeding_request_service import BreedingRequestService
from utils.pagination import PaginatedResponse, PaginationParams, paginate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedResponse[BreedingRequestPublic]],
    summary="Search breeding requests",
    description="Search for active breeding requests with filters"
)
async def search_breeding_requests(
    q: Optional[str] = Query(None, description="Search in title, description, breed"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    is_pedigree: Optional[bool] = Query(None, description="Filter pedigree pets"),
    has_papers: Optional[bool] = Query(None, description="Filter pets with papers"),
    health_certified: Optional[bool] = Query(None, description="Filter health certified pets"),
    pagination: PaginationParams = Depends(),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Search breeding requests with advanced filtering."""
    filters = {
        "search_term": q,
        "category_id": category_id,
        "city_id": city_id,
        "is_pedigree": is_pedigree,
        "has_papers": has_papers,
        "health_certified": health_certified,
        "status": "active"
    }
    
    logger.info(f"Searching breeding requests with filters: {filters}")
    
    requests, total = await service.search_requests(
        filters=filters,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    paginated = paginate(requests, total, pagination.page, pagination.page_size)
    
    return ApiResponse(
        success=True,
        data=paginated,
        message=f"Found {total} breeding requests"
    )


@router.post(
    "/",
    response_model=ApiResponse[BreedingRequest],
    status_code=status.HTTP_201_CREATED,
    summary="Create breeding request",
    description="Create a new breeding request for your pet"
)
async def create_breeding_request(
    request_in: BreedingRequestCreate,
    current_user: User = Depends(get_current_active_user),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Create a new breeding request."""
    logger.info(f"Creating breeding request for pet {request_in.pet_id} by user {current_user.id}")
    
    request_data = request_in.model_dump()
    request_data["owner_id"] = current_user.id
    request_data["status"] = "active"
    
    breeding_request = await service.create(request_data)
    
    return ApiResponse(
        success=True,
        data=breeding_request,
        message="Breeding request created successfully"
    )


@router.get(
    "/",
    response_model=ApiResponse[PaginatedResponse[BreedingRequestPublic]],
    summary="List active breeding requests",
    description="Get all active breeding requests"
)
async def list_breeding_requests(
    pagination: PaginationParams = Depends(),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """List all active breeding requests."""
    logger.info(f"Listing breeding requests")
    
    requests = await service.get_active_requests(
        skip=pagination.skip,
        limit=pagination.limit,
        category_id=category_id,
        city_id=city_id
    )
    
    total = await service.count({"status": "active"})
    paginated = paginate(requests, total, pagination.page, pagination.page_size)
    
    return ApiResponse(success=True, data=paginated)


@router.get(
    "/my-requests",
    response_model=ApiResponse[List[BreedingRequest]],
    summary="Get my breeding requests",
    description="Get all breeding requests created by current user"
)
async def list_my_breeding_requests(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Get current user's breeding requests."""
    logger.info(f"Listing breeding requests for user {current_user.id}")
    
    requests = await service.get_user_requests(
        owner_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return ApiResponse(success=True, data=requests)


@router.get(
    "/{request_id}",
    response_model=ApiResponse[BreedingRequest],
    summary="Get breeding request",
    description="Get details of a specific breeding request"
)
async def get_breeding_request(
    request_id: int,
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Get a specific breeding request with details."""
    logger.info(f"Getting breeding request {request_id}")
    
    breeding_request = await service.get_request_with_details(request_id)
    
    if not breeding_request:
        raise NotFoundException("Breeding request")
    
    return ApiResponse(success=True, data=breeding_request)


@router.get(
    "/{request_id}/matches",
    response_model=ApiResponse[List[BreedingRequestPublic]],
    summary="Find matches",
    description="Find potential breeding matches for a request"
)
async def find_breeding_matches(
    request_id: int,
    limit: int = Query(20, ge=1, le=100, description="Number of matches to return"),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Find potential breeding matches for a request."""
    logger.info(f"Finding matches for breeding request {request_id}")
    
    # Verify request exists
    breeding_request = await service.get_by_id(request_id)
    if not breeding_request:
        raise NotFoundException("Breeding request")
    
    matches = await service.find_matches(request_id, skip=0, limit=limit)
    
    return ApiResponse(
        success=True,
        data=matches,
        message=f"Found {len(matches)} potential matches"
    )


@router.put(
    "/{request_id}",
    response_model=ApiResponse[BreedingRequest],
    summary="Update breeding request",
    description="Update your breeding request"
)
async def update_breeding_request(
    request_id: int,
    request_in: BreedingRequestUpdate,
    current_user: User = Depends(get_current_active_user),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Update a breeding request."""
    logger.info(f"Updating breeding request {request_id}")
    
    # Verify ownership
    if not await service.verify_owner(request_id, current_user.id):
        raise PermissionDeniedException("update this breeding request")
    
    update_data = request_in.model_dump(exclude_unset=True)
    breeding_request = await service.update(request_id, update_data)
    
    if not breeding_request:
        raise NotFoundException("Breeding request")
    
    return ApiResponse(
        success=True,
        data=breeding_request,
        message="Breeding request updated successfully"
    )


@router.patch(
    "/{request_id}/status",
    response_model=ApiResponse[BreedingRequest],
    summary="Update request status",
    description="Update the status of your breeding request"
)
async def update_breeding_request_status(
    request_id: int,
    status_update: BreedingRequestStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Update breeding request status."""
    logger.info(f"Updating status of breeding request {request_id} to {status_update.status}")
    
    breeding_request = await service.update_status(
        request_id,
        status_update.status,
        current_user.id
    )
    
    if not breeding_request:
        raise PermissionDeniedException("update this breeding request")
    
    return ApiResponse(
        success=True,
        data=breeding_request,
        message=f"Status updated to {status_update.status}"
    )


@router.delete(
    "/{request_id}",
    response_model=ApiResponse[MessageResponse],
    summary="Delete breeding request",
    description="Delete your breeding request"
)
async def delete_breeding_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    service: BreedingRequestService = Depends(get_breeding_request_service)
):
    """Delete a breeding request."""
    logger.info(f"Deleting breeding request {request_id}")
    
    # Verify ownership
    if not await service.verify_owner(request_id, current_user.id):
        raise PermissionDeniedException("delete this breeding request")
    
    success = await service.delete(request_id)
    
    if not success:
        raise NotFoundException("Breeding request")
    
    return ApiResponse(
        success=True,
        data={"message": "Breeding request deleted successfully"},
        message="Breeding request deleted"
    )
