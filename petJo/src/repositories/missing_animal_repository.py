"""Repository for missing animal operations."""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.missing_animal import MissingAnimal
from repositories.base import BaseRepository


class MissingAnimalRepository(BaseRepository[MissingAnimal]):
    """Repository for missing animal database operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(MissingAnimal, db)
    
    async def get_by_owner(self, owner_id: str) -> List[MissingAnimal]:
        """Get all missing animal reports by owner."""
        result = await self.db.execute(
            select(MissingAnimal)
            .options(selectinload(MissingAnimal.city))
            .filter(MissingAnimal.owner_id == owner_id)
            .order_by(MissingAnimal.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_active_reports(
        self,
        skip: int = 0,
        limit: int = 20,
        city_id: Optional[int] = None,
        animal_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MissingAnimal]:
        """Get active missing animal reports with optional filters."""
        query = (
            select(MissingAnimal)
            .options(selectinload(MissingAnimal.city))
            .filter(MissingAnimal.is_active == True)
        )
        
        # Apply filters
        if city_id:
            query = query.filter(MissingAnimal.city_id == city_id)
        
        if animal_type:
            query = query.filter(MissingAnimal.animal_type == animal_type.lower())
        
        if status:
            query = query.filter(MissingAnimal.status == status)
        else:
            # Default: only show missing and sighted (not found/reunited)
            query = query.filter(MissingAnimal.status.in_(["missing", "sighted"]))
        
        query = query.order_by(MissingAnimal.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_active_reports(
        self,
        city_id: Optional[int] = None,
        animal_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count active missing animal reports with filters."""
        query = select(func.count(MissingAnimal.id)).filter(
            MissingAnimal.is_active == True
        )
        
        if city_id:
            query = query.filter(MissingAnimal.city_id == city_id)
        
        if animal_type:
            query = query.filter(MissingAnimal.animal_type == animal_type.lower())
        
        if status:
            query = query.filter(MissingAnimal.status == status)
        else:
            query = query.filter(MissingAnimal.status.in_(["missing", "sighted"]))
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def search_reports(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20,
        city_id: Optional[int] = None
    ) -> List[MissingAnimal]:
        """Search missing animal reports by name, breed, description."""
        search_pattern = f"%{search_term.lower()}%"
        
        query = (
            select(MissingAnimal)
            .options(selectinload(MissingAnimal.city))
            .filter(
                MissingAnimal.is_active == True,
                MissingAnimal.status.in_(["missing", "sighted"]),
                or_(
                    func.lower(MissingAnimal.pet_name).like(search_pattern),
                    func.lower(MissingAnimal.breed).like(search_pattern),
                    func.lower(MissingAnimal.color).like(search_pattern),
                    func.lower(MissingAnimal.description).like(search_pattern),
                    func.lower(MissingAnimal.distinguishing_features).like(search_pattern)
                )
            )
        )
        
        if city_id:
            query = query.filter(MissingAnimal.city_id == city_id)
        
        query = query.order_by(MissingAnimal.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_reports(
        self,
        days: int = 7,
        city_id: Optional[int] = None,
        limit: int = 10
    ) -> List[MissingAnimal]:
        """Get recent missing animal reports within specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(MissingAnimal)
            .options(selectinload(MissingAnimal.city))
            .filter(
                MissingAnimal.is_active == True,
                MissingAnimal.status.in_(["missing", "sighted"]),
                MissingAnimal.created_at >= cutoff_date
            )
        )
        
        if city_id:
            query = query.filter(MissingAnimal.city_id == city_id)
        
        query = query.order_by(MissingAnimal.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_status(
        self,
        report_id: int,
        status: str
    ) -> Optional[MissingAnimal]:
        """Update the status of a missing animal report."""
        report = await self.get(report_id)
        if not report:
            return None
        
        report.status = status
        if status in ["found", "reunited"]:
            report.found_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(report)
        return report
    
    async def get_by_pet_id(self, pet_id: str) -> List[MissingAnimal]:
        """Get all missing animal reports for a specific pet."""
        result = await self.db.execute(
            select(MissingAnimal)
            .filter(MissingAnimal.pet_id == pet_id)
            .order_by(MissingAnimal.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_statistics(self, city_id: Optional[int] = None) -> dict:
        """Get statistics about missing animal reports."""
        base_query = select(func.count(MissingAnimal.id))
        
        if city_id:
            base_query = base_query.filter(MissingAnimal.city_id == city_id)
        
        # Total active reports
        active_query = base_query.filter(
            MissingAnimal.is_active == True,
            MissingAnimal.status.in_(["missing", "sighted"])
        )
        total_active = (await self.db.execute(active_query)).scalar_one()
        
        # Total found
        found_query = base_query.filter(MissingAnimal.status.in_(["found", "reunited"]))
        total_found = (await self.db.execute(found_query)).scalar_one()
        
        # Recent (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent_query = base_query.filter(
            MissingAnimal.is_active == True,
            MissingAnimal.created_at >= cutoff
        )
        recent_reports = (await self.db.execute(recent_query)).scalar_one()
        
        return {
            "active_reports": total_active,
            "total_found": total_found,
            "recent_reports": recent_reports
        }
