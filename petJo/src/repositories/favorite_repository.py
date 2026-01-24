"""Favorite repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.favorite import Favorite
from repositories.base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    """Repository for Favorite database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize favorite repository."""
        super().__init__(Favorite, db)
    
    async def get_user_favorites(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Favorite]:
        """
        Get all favorites for a user with pet details.
        
        Args:
            user_id: UUID of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of user's favorites with pet details.
        """
        query = (
            select(Favorite)
            .options(selectinload(Favorite.pet))
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_user_and_pet(
        self,
        user_id: UUID,
        pet_id: UUID
    ) -> Optional[Favorite]:
        """
        Get favorite by user and pet.
        
        Args:
            user_id: UUID of the user.
            pet_id: UUID of the pet.
            
        Returns:
            Favorite if exists, None otherwise.
        """
        query = select(Favorite).where(
            and_(
                Favorite.user_id == user_id,
                Favorite.pet_id == pet_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def delete_by_user_and_pet(
        self,
        user_id: UUID,
        pet_id: UUID
    ) -> bool:
        """
        Delete favorite by user and pet.
        
        Args:
            user_id: UUID of the user.
            pet_id: UUID of the pet.
            
        Returns:
            True if deleted, False otherwise.
        """
        favorite = await self.get_by_user_and_pet(user_id, pet_id)
        if not favorite:
            return False
        
        await self.db.delete(favorite)
        await self.db.commit()
        return True
    
    async def is_favorited(
        self,
        user_id: UUID,
        pet_id: UUID
    ) -> bool:
        """
        Check if pet is favorited by user.
        
        Args:
            user_id: UUID of the user.
            pet_id: UUID of the pet.
            
        Returns:
            True if favorited, False otherwise.
        """
        favorite = await self.get_by_user_and_pet(user_id, pet_id)
        return favorite is not None
