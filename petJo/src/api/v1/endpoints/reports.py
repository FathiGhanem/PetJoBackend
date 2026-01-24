"""Reports endpoints."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_active_user, get_current_superuser, get_report_service
from models.user import User
from schemas.common import ApiResponse
from schemas.report import Report, ReportCreate
from services.report_service import ReportService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[Report],
    status_code=status.HTTP_201_CREATED,
    summary="Create report",
    description="Report inappropriate content or behavior"
)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Create a new report."""
    logger.warning(
        f"User {current_user.id} reporting {report_in.target_type} "
        f"{report_in.target_id}: {report_in.reason[:50]}..."
    )
    
    report_data = report_in.model_dump()
    report_data["reporter_id"] = current_user.id
    
    report = await report_service.create(report_data)
    
    return ApiResponse(
        success=True,
        data=report,
        message="Report submitted successfully. Our team will review it."
    )


@router.get(
    "/",
    response_model=ApiResponse[List[Report]],
    summary="Get all reports (Admin only)",
    description="Get all reports for moderation"
)
async def get_all_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    report_service: ReportService = Depends(get_report_service)
):
    """Get all reports. Admin only."""
    logger.info(f"Admin {current_user.email} fetching all reports")
    
    reports = await report_service.get_all_reports(skip, limit)
    
    return ApiResponse(
        success=True,
        data=reports,
        message=f"Retrieved {len(reports)} reports"
    )


@router.get(
    "/{target_type}/{target_id}",
    response_model=ApiResponse[List[Report]],
    summary="Get reports for target (Admin only)",
    description="Get all reports for a specific target"
)
async def get_reports_by_target(
    target_type: str,
    target_id: int,
    current_user: User = Depends(get_current_superuser),
    report_service: ReportService = Depends(get_report_service)
):
    """Get reports for a specific target. Admin only."""
    logger.info(f"Admin {current_user.email} fetching reports for {target_type} {target_id}")
    
    if target_type not in ["pet", "advertisement", "profile"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target type. Must be: pet, advertisement, or profile"
        )
    
    reports = await report_service.get_reports_by_target(target_type, target_id)
    
    return ApiResponse(
        success=True,
        data=reports,
        message=f"Retrieved {len(reports)} reports for {target_type} {target_id}"
    )
