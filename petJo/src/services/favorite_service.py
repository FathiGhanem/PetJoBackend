"""Favorite service for business logic."""
from typing import List
from uuid import UUID

from repositories.favorite_repository import FavoriteRepository
from services.base import BaseService


class FavoriteService(BaseService[None, FavoriteRepository]):
    """Service for Favorite business logic."""
    
    async def get_user_favorites(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get user's favorite pets.
        
        Args:
            user_id: UUID of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of favorites with pet details.
        """
        return await self.repository.get_user_favorites(user_id, skip, limit)
    
    async def add_favorite(
        self,
        user_id: UUID,
        pet_id: UUID
    ):
        """
        Add pet to favorites.
        
        Args:
            user_id: UUID of the user.
            pet_id: UUID of the pet.
            
        Returns:
            Created favorite.
        """
        # Check if already favorited
        existing = await self.repository.get_by_user_and_pet(user_id, pet_id)
        if existing:
            return existing
        
        return await self.repository.create({
            "user_id": user_id,
            "pet_id": pet_id
        })
    
    async def remove_favorite(
        self,
        user_id: UUID,
        pet_id: UUID
    ) -> bool:
        """
        Remove pet from favorites.
        
        Args:
            user_id: UUID of the user.
            pet_id: UUID of the pet.
            
        Returns:
            True if removed, False if not found.
        """
        return await self.repository.delete_by_user_and_pet(user_id, pet_id)
    
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
        return await self.repository.is_favorited(user_id, pet_id)
