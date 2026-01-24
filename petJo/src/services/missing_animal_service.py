"""Service layer for missing animal operations."""
import logging
from typing import List, Optional
from fastapi import HTTPException, status

from repositories.missing_animal_repository import MissingAnimalRepository
from schemas.missing_animal import MissingAnimalCreate, MissingAnimalUpdate
from models.missing_animal import MissingAnimal

logger = logging.getLogger(__name__)


class MissingAnimalService:
    """Service for missing animal business logic."""
    
    def __init__(self, repository: MissingAnimalRepository):
        self.repository = repository
    
    async def create_report(
        self,
        owner_id: str,
        report_data: MissingAnimalCreate
    ) -> MissingAnimal:
        """Create a new missing animal report."""
        logger.info(f"Creating missing animal report for owner: {owner_id}")
        
        # Prepare data
        data = report_data.model_dump()
        data["owner_id"] = owner_id
        
        # Normalize animal type
        if data.get("animal_type"):
            data["animal_type"] = data["animal_type"].lower()
        
        report = await self.repository.create(data)
        logger.info(f"Missing animal report created: {report.id}")
        return report
    
    async def get_user_reports(self, owner_id: str) -> List[MissingAnimal]:
        """Get all missing animal reports for a user."""
        return await self.repository.get_by_owner(owner_id)
    
    async def get_public_reports(
        self,
        skip: int = 0,
        limit: int = 20,
        city_id: Optional[int] = None,
        animal_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MissingAnimal]:
        """Get public missing animal reports with filters."""
        return await self.repository.get_active_reports(
            skip=skip,
            limit=limit,
            city_id=city_id,
            animal_type=animal_type,
            status=status
        )
    
    async def count_reports(
        self,
        city_id: Optional[int] = None,
        animal_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count active missing animal reports."""
        return await self.repository.count_active_reports(
            city_id=city_id,
            animal_type=animal_type,
            status=status
        )
    
    async def search_reports(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20,
        city_id: Optional[int] = None
    ) -> List[MissingAnimal]:
        """Search missing animal reports."""
        if not search_term or len(search_term.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term must be at least 2 characters"
            )
        
        return await self.repository.search_reports(
            search_term=search_term.strip(),
            skip=skip,
            limit=limit,
            city_id=city_id
        )
    
    async def update_report(
        self,
        report_id: int,
        owner_id: str,
        update_data: MissingAnimalUpdate
    ) -> MissingAnimal:
        """Update a missing animal report."""
        report = await self.repository.get(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missing animal report not found"
            )
        
        # Verify ownership
        if str(report.owner_id) != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this report"
            )
        
        # Update fields
        data = update_data.model_dump(exclude_unset=True)
        
        # Normalize animal type
        if "animal_type" in data and data["animal_type"]:
            data["animal_type"] = data["animal_type"].lower()
        
        updated_report = await self.repository.update(report_id, data)
        logger.info(f"Missing animal report updated: {report_id}")
        return updated_report
    
    async def update_status(
        self,
        report_id: int,
        owner_id: str,
        new_status: str
    ) -> MissingAnimal:
        """Update the status of a missing animal report."""
        report = await self.repository.get(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missing animal report not found"
            )
        
        # Verify ownership
        if str(report.owner_id) != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this report"
            )
        
        # Validate status transition
        valid_statuses = ["missing", "sighted", "found", "reunited", "closed"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        updated_report = await self.repository.update_status(report_id, new_status)
        logger.info(f"Missing animal report {report_id} status updated to: {new_status}")
        return updated_report
    
    async def deactivate_report(
        self,
        report_id: int,
        owner_id: str
    ) -> MissingAnimal:
        """Deactivate/close a missing animal report."""
        report = await self.repository.get(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missing animal report not found"
            )
        
        # Verify ownership
        if str(report.owner_id) != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to close this report"
            )
        
        updated_report = await self.repository.update(report_id, {"is_active": False})
        logger.info(f"Missing animal report deactivated: {report_id}")
        return updated_report
    
    async def get_recent_reports(
        self,
        days: int = 7,
        city_id: Optional[int] = None,
        limit: int = 10
    ) -> List[MissingAnimal]:
        """Get recent missing animal reports."""
        return await self.repository.get_recent_reports(
            days=days,
            city_id=city_id,
            limit=limit
        )
    
    async def get_statistics(self, city_id: Optional[int] = None) -> dict:
        """Get statistics about missing animal reports."""
        return await self.repository.get_statistics(city_id=city_id)
    
    async def get(self, report_id: int) -> MissingAnimal:
        """Get a missing animal report by ID."""
        report = await self.repository.get(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Missing animal report not found"
            )
        
        return report
