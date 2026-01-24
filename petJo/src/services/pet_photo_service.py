"""Pet photo service for business logic."""
from typing import List
from uuid import UUID

from repositories.pet_photo_repository import PetPhotoRepository
from services.base import BaseService


class PetPhotoService(BaseService[None, PetPhotoRepository]):
    """Service for PetPhoto business logic."""
    
    async def get_pet_photos(
        self,
        pet_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all photos for a pet.
        
        Args:
            pet_id: UUID of the pet.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of pet photos.
        """
        return await self.repository.get_pet_photos(pet_id, skip, limit)
