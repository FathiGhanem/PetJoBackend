"""Report repository for database operations."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.report import Report
from repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Repository for Report database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize report repository."""
        super().__init__(Report, db)
    
    async def get_by_target(
        self,
        target_type: str,
        target_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """
        Get all reports for a specific target.
        
        Args:
            target_type: Type of target (pet, advertisement, profile).
            target_id: ID of the target.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of reports.
        """
        query = (
            select(Report)
            .where(Report.target_type == target_type, Report.target_id == target_id)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_reports(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """
        Get all reports.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of all reports.
        """
        query = (
            select(Report)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
