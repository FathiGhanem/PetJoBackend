"""API endpoints for missing animal reports."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status

from core.storage import get_storage_service
from schemas.missing_animal import (
    MissingAnimalCreate,
    MissingAnimalUpdate,
    MissingAnimalStatusUpdate,
    MissingAnimalPublic
)
from schemas.common import ApiResponse, PaginatedResponse
from dependencies import get_missing_animal_service, get_current_user_id
from services.missing_animal_service import MissingAnimalService
from core.rate_limit import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[MissingAnimalPublic],
    status_code=status.HTTP_201_CREATED,
    summary="Report a missing animal",
    description="Create a new missing animal report with optional photos"
)
@limiter.limit(RATE_LIMITS["default"])
async def create_missing_report(
    request: Request,
    animal_name: str = Form(...),
    animal_type: str = Form(...),
    breed: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    city_id: int = Form(...),
    last_seen_location: str = Form(...),
    last_seen_date: str = Form(...),
    description: str = Form(...),
    contact_phone: str = Form(...),
    contact_email: Optional[str] = Form(None),
    reward_amount: Optional[float] = Form(None),
    photos: Optional[List[UploadFile]] = File(None, description="Photos of the missing animal (max 5)"),
    user_id: str = Depends(get_current_user_id),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Report a missing animal with optional photo uploads."""
    logger.info(f"Creating missing animal report for user: {user_id}")
    
    # Upload photos if provided
    photo_url = None
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
                    folder="missing-animals"
                )
                
                if not photo_url:
                    photo_url = url  # Use first photo as main
                
                logger.info(f"Uploaded missing animal photo: {url}")
            except Exception as e:
                logger.error(f"Failed to upload photo {photo.filename}: {e}")
                continue
    
    # Create report data
    report_data = MissingAnimalCreate(
        animal_name=animal_name,
        animal_type=animal_type,
        breed=breed,
        color=color,
        age=age,
        gender=gender,
        city_id=city_id,
        last_seen_location=last_seen_location,
        last_seen_date=last_seen_date,
        description=description,
        contact_phone=contact_phone,
        contact_email=contact_email,
        reward_amount=reward_amount,
        photo_url=photo_url
    )
    
    report = await service.create_report(owner_id=user_id, report_data=report_data)
    
    return ApiResponse(
        success=True,
        data=MissingAnimalPublic.model_validate(report),
        message="Missing animal report created successfully"
    )


@router.get(
    "/",
    response_model=ApiResponse[PaginatedResponse[MissingAnimalPublic]],
    summary="List missing animals",
    description="Get list of active missing animal reports"
)
@limiter.limit(RATE_LIMITS["public"])
async def list_missing_reports(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    animal_type: Optional[str] = Query(None, description="Filter by animal type (dog, cat, etc.)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """List active missing animal reports."""
    skip = (page - 1) * page_size
    
    reports = await service.get_public_reports(
        skip=skip,
        limit=page_size,
        city_id=city_id,
        animal_type=animal_type,
        status=status
    )
    
    total = await service.count_reports(
        city_id=city_id,
        animal_type=animal_type,
        status=status
    )
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=[MissingAnimalPublic.model_validate(r) for r in reports],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    )


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedResponse[MissingAnimalPublic]],
    summary="Search missing animals",
    description="Search missing animal reports by keywords"
)
@limiter.limit(RATE_LIMITS["search"])
async def search_missing_reports(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Search missing animal reports."""
    skip = (page - 1) * page_size
    
    reports = await service.search_reports(
        search_term=q,
        skip=skip,
        limit=page_size,
        city_id=city_id
    )
    
    return ApiResponse(
        success=True,
        data=PaginatedResponse(
            items=[MissingAnimalPublic.model_validate(r) for r in reports],
            total=len(reports),
            page=page,
            page_size=page_size,
            pages=1  # Search doesn't have total count
        )
    )


@router.get(
    "/my-reports",
    response_model=ApiResponse[List[MissingAnimalPublic]],
    summary="Get my missing reports",
    description="Get all missing animal reports created by current user"
)
@limiter.limit(RATE_LIMITS["default"])
async def get_my_reports(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Get user's missing animal reports."""
    reports = await service.get_user_reports(owner_id=user_id)
    
    return ApiResponse(
        success=True,
        data=[MissingAnimalPublic.model_validate(r) for r in reports]
    )


@router.get(
    "/recent",
    response_model=ApiResponse[List[MissingAnimalPublic]],
    summary="Get recent missing reports",
    description="Get recent missing animal reports (last 7 days by default)"
)
@limiter.limit(RATE_LIMITS["public"])
async def get_recent_reports(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    limit: int = Query(10, ge=1, le=50, description="Number of reports"),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Get recent missing animal reports."""
    reports = await service.get_recent_reports(days=days, city_id=city_id, limit=limit)
    
    return ApiResponse(
        success=True,
        data=[MissingAnimalPublic.model_validate(r) for r in reports]
    )


@router.get(
    "/statistics",
    response_model=ApiResponse[dict],
    summary="Get missing animals statistics",
    description="Get statistics about missing animal reports"
)
@limiter.limit(RATE_LIMITS["public"])
async def get_statistics(
    request: Request,
    city_id: Optional[int] = Query(None, description="Filter by city"),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Get missing animal statistics."""
    stats = await service.get_statistics(city_id=city_id)
    
    return ApiResponse(
        success=True,
        data=stats
    )


@router.get(
    "/{report_id}",
    response_model=ApiResponse[MissingAnimalPublic],
    summary="Get missing report details",
    description="Get details of a specific missing animal report"
)
@limiter.limit(RATE_LIMITS["default"])
async def get_missing_report(
    request: Request,
    report_id: int,
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Get a specific missing animal report."""
    report = await service.get(report_id)
    
    return ApiResponse(
        success=True,
        data=MissingAnimalPublic.model_validate(report)
    )


@router.put(
    "/{report_id}",
    response_model=ApiResponse[MissingAnimalPublic],
    summary="Update missing report",
    description="Update a missing animal report (owner only)"
)
@limiter.limit(RATE_LIMITS["default"])
async def update_missing_report(
    request: Request,
    report_id: int,
    update_data: MissingAnimalUpdate,
    user_id: str = Depends(get_current_user_id),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Update a missing animal report."""
    report = await service.update_report(
        report_id=report_id,
        owner_id=user_id,
        update_data=update_data
    )
    
    return ApiResponse(
        success=True,
        data=MissingAnimalPublic.model_validate(report),
        message="Missing animal report updated successfully"
    )


@router.patch(
    "/{report_id}/status",
    response_model=ApiResponse[MissingAnimalPublic],
    summary="Update report status",
    description="Update the status of a missing animal report (owner only)"
)
@limiter.limit(RATE_LIMITS["default"])
async def update_report_status(
    request: Request,
    report_id: int,
    status_data: MissingAnimalStatusUpdate,
    user_id: str = Depends(get_current_user_id),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Update missing animal report status."""
    report = await service.update_status(
        report_id=report_id,
        owner_id=user_id,
        new_status=status_data.status
    )
    
    return ApiResponse(
        success=True,
        data=MissingAnimalPublic.model_validate(report),
        message=f"Report status updated to: {status_data.status}"
    )


@router.delete(
    "/{report_id}",
    response_model=ApiResponse[dict],
    summary="Close missing report",
    description="Deactivate/close a missing animal report (owner only)"
)
@limiter.limit(RATE_LIMITS["default"])
async def close_missing_report(
    request: Request,
    report_id: int,
    user_id: str = Depends(get_current_user_id),
    service: MissingAnimalService = Depends(get_missing_animal_service)
):
    """Close a missing animal report."""
    await service.deactivate_report(report_id=report_id, owner_id=user_id)
    
    return ApiResponse(
        success=True,
        data={"message": "Missing animal report closed successfully"},
        message="Report closed successfully"
    )
