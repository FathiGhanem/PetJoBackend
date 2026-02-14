"""Advertisement endpoints for users and admins."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from dependencies import get_current_user, get_current_superuser
from models.user import User
from schemas.advertisement import (
    Advertisement,
    AdvertisementCreate,
    AdvertisementUpdate,
    AdvertisementWithUser,
    AdvertisementReview
)
from schemas.common import ApiResponse, PaginatedResponse
from services.advertisement_service import AdvertisementService

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[Advertisement],
    status_code=status.HTTP_201_CREATED,
    summary="Submit advertisement request"
)
async def create_advertisement(
    ad_data: AdvertisementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new advertisement request.
    
    Users can submit advertisement requests with:
    - Title (5-200 characters)
    - Description (10-2000 characters)
    - Contact phone (optional)
    
    The request will be reviewed by administrators.
    """
    service = AdvertisementService(db)
    ad = await service.create_advertisement(
        user_id=current_user.id,
        title=ad_data.title,
        description=ad_data.description,
        contact_phone=ad_data.contact_phone
    )
    
    return ApiResponse(
        success=True,
        data=ad,
        message="Advertisement request submitted successfully. It will be reviewed by administrators."
    )


@router.get(
    "/my-requests",
    response_model=ApiResponse[List[Advertisement]],
    summary="Get my advertisement requests"
)
async def get_my_advertisements(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all advertisement requests submitted by the current user.
    
    Returns a paginated list of your advertisement requests.
    """
    service = AdvertisementService(db)
    skip = (page - 1) * page_size
    
    ads = await service.get_user_advertisements(
        user_id=current_user.id,
        skip=skip,
        limit=page_size
    )
    
    total = await service.count_user_advertisements(current_user.id)
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=ads,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        ),
        message=f"Found {len(ads)} advertisement requests"
    )


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedResponse[Advertisement]],
    summary="Search advertisements (Admin)"
)
async def search_advertisements(
    q: Optional[str] = Query(None, description="Search term"),
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Search advertisements by title or description with status filter (admin only).
    """
    service = AdvertisementService(db)
    skip = (page - 1) * page_size
    
    ads = await service.search_advertisements(
        search_term=q,
        status=status,
        skip=skip,
        limit=page_size
    )
    
    total = await service.count_all()
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=ads,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        ),
        message=f"Found {len(ads)} advertisements"
    )


@router.get(
    "/{ad_id}",
    response_model=ApiResponse[Advertisement],
    summary="Get advertisement by ID"
)
async def get_advertisement(
    ad_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific advertisement by ID.
    
    Users can only view their own advertisements unless they are admins.
    """
    service = AdvertisementService(db)
    ad = await service.get_advertisement_by_id(ad_id)
    
    # Check if user can view (owner or admin)
    if ad.user_id != current_user.id and not current_user.is_superuser:
        from exceptions import ForbiddenException
        raise ForbiddenException("You can only view your own advertisements")
    
    return ApiResponse(
        success=True,
        data=ad,
        message="Advertisement retrieved successfully"
    )


@router.patch(
    "/{ad_id}",
    response_model=ApiResponse[Advertisement],
    summary="Update advertisement"
)
async def update_advertisement(
    ad_id: int,
    update_data: AdvertisementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update your advertisement request.
    
    Only the owner can update their advertisement.
    """
    service = AdvertisementService(db)
    
    # Filter out None values
    update_dict = update_data.model_dump(exclude_unset=True)
    
    ad = await service.update_advertisement(
        ad_id=ad_id,
        user_id=current_user.id,
        update_data=update_dict
    )
    
    return ApiResponse(
        success=True,
        data=ad,
        message="Advertisement updated successfully"
    )


@router.delete(
    "/{ad_id}",
    response_model=ApiResponse[None],
    summary="Delete advertisement"
)
async def delete_advertisement(
    ad_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an advertisement request.
    
    Only the owner can delete their advertisement.
    """
    service = AdvertisementService(db)
    
    await service.delete_advertisement(
        ad_id=ad_id,
        user_id=current_user.id
    )
    
    return ApiResponse(
        success=True,
        data=None,
        message="Advertisement deleted successfully"
    )


# Admin endpoints
@router.get(
    "/admin/pending",
    response_model=ApiResponse[PaginatedResponse[Advertisement]],
    summary="Get pending advertisements (Admin)"
)
async def admin_get_pending_advertisements(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending advertisement requests awaiting review (admin only).
    """
    service = AdvertisementService(db)
    skip = (page - 1) * page_size
    
    ads_with_users = await service.get_pending_with_users(skip=skip, limit=page_size)
    total = await service.count_pending()
    
    # Transform to response format with user info
    ads_response = []
    for ad, user_email, user_name in ads_with_users:
        ad_dict = {
            "id": ad.id,
            "user_id": ad.user_id,
            "title": ad.title,
            "description": ad.description,
            "contact_phone": ad.contact_phone,
            "status": ad.status,
            "admin_notes": ad.admin_notes,
            "created_at": ad.created_at,
            "updated_at": ad.updated_at,
            "reviewed_at": ad.reviewed_at,
            "user_email": user_email,
            "user_name": user_name
        }
        ads_response.append(ad_dict)
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=ads_response,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        ),
        message=f"Found {total} pending advertisement requests"
    )


@router.get(
    "/admin/all",
    response_model=ApiResponse[PaginatedResponse[Advertisement]],
    summary="Get all advertisements (Admin)"
)
async def admin_get_all_advertisements(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all advertisement requests (admin only).
    
    Returns a paginated list of all advertisement requests from all users.
    """
    service = AdvertisementService(db)
    skip = (page - 1) * page_size
    
    # Get with user information
    ads_with_users = await service.get_all_with_users(skip=skip, limit=page_size)
    
    # Transform to response format
    ads_response = []
    for ad, user_email, user_name in ads_with_users:
        ad_dict = {
            "id": ad.id,
            "user_id": ad.user_id,
            "title": ad.title,
            "description": ad.description,
            "contact_phone": ad.contact_phone,
            "status": ad.status,
            "admin_notes": ad.admin_notes,
            "created_at": ad.created_at,
            "updated_at": ad.updated_at,
            "reviewed_at": ad.reviewed_at,
            "user_email": user_email,
            "user_name": user_name
        }
        ads_response.append(ad_dict)
    
    total = await service.count_all()
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=ads_response,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        ),
        message=f"Found {total} advertisement requests"
    )


@router.post(
    "/admin/{ad_id}/review",
    response_model=ApiResponse[Advertisement],
    summary="Review advertisement (Admin)"
)
async def admin_review_advertisement(
    ad_id: int,
    review_data: AdvertisementReview,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Review an advertisement - approve or reject (admin only).
    
    - **approved**: Advertisement is approved and can be published
    - **rejected**: Advertisement is rejected with optional feedback
    """
    service = AdvertisementService(db)
    
    ad = await service.review_advertisement(
        ad_id=ad_id,
        status=review_data.status,
        admin_notes=review_data.admin_notes
    )
    
    return ApiResponse(
        success=True,
        data=ad,
        message=f"Advertisement {review_data.status} successfully"
    )


@router.delete(
    "/admin/{ad_id}",
    response_model=ApiResponse[None],
    summary="Delete advertisement (Admin)"
)
async def admin_delete_advertisement(
    ad_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete any advertisement request (admin only).
    """
    service = AdvertisementService(db)
    
    await service.delete_advertisement(
        ad_id=ad_id,
        user_id=current_user.id,
        is_admin=True
    )
    
    return ApiResponse(
        success=True,
        data=None,
        message="Advertisement deleted successfully"
    )
