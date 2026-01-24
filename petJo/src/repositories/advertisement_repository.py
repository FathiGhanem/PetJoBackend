"""Repository for advertisement database operations."""
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from uuid import UUID

from models.advertisement import Advertisement
from models.user import User
from repositories.base import BaseRepository


class AdvertisementRepository(BaseRepository[Advertisement]):
    """Repository for advertisement CRUD operations."""
    
    def __init__(self):
        super().__init__(Advertisement)
    
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Get all advertisements by user ID."""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_all_with_user(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[tuple]:
        """Get all advertisements with user information."""
        query = (
            select(
                Advertisement,
                User.email,
                User.full_name
            )
            .join(User, Advertisement.user_id == User.id)
            .order_by(Advertisement.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.all())
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count advertisements by user."""
        query = select(func.count()).select_from(self.model).where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def search(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Search advertisements by title or description with optional status filter."""
        query = select(self.model)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                (self.model.title.ilike(search_pattern)) |
                (self.model.description.ilike(search_pattern))
            )
        
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_count(self) -> int:
        """Count pending advertisements."""
        query = select(func.count()).select_from(self.model).where(self.model.status == "pending")
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Get advertisements by status."""
        query = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
