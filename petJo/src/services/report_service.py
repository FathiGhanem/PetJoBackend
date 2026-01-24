"""Report service for business logic."""
from typing import List

from repositories.report_repository import ReportRepository
from services.base import BaseService


class ReportService(BaseService[None, ReportRepository]):
    """Service for Report business logic."""
    
    async def get_reports_by_target(
        self,
        target_type: str,
        target_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all reports for a specific target.
        
        Args:
            target_type: Type of target.
            target_id: ID of the target.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of reports.
        """
        return await self.repository.get_by_target(target_type, target_id, skip, limit)
    
    async def get_all_reports(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all reports.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of all reports.
        """
        return await self.repository.get_all_reports(skip, limit)
