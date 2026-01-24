"""Hero service for business logic."""
from typing import List

from repositories.hero_repository import HeroRepository
from services.base import BaseService


class HeroService(BaseService[None, HeroRepository]):
    """Service for Hero business logic."""
    
    async def get_all_heroes(self, skip: int = 0, limit: int = 100) -> List:
        """
        Get all hero items.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of hero items.
        """
        return await self.repository.get_all(skip, limit)
