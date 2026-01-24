"""Hero repository for database operations."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.hero import Hero
from repositories.base import BaseRepository


class HeroRepository(BaseRepository[Hero]):
    """Repository for Hero database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize hero repository."""
        super().__init__(Hero, db)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Hero]:
        """
        Get all hero items.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of hero items.
        """
        query = select(Hero).order_by(Hero.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
