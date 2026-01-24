"""Pet photo repository for database operations."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pet_photo import PetPhoto
from repositories.base import BaseRepository


class PetPhotoRepository(BaseRepository[PetPhoto]):
    """Repository for PetPhoto database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize pet photo repository."""
        super().__init__(PetPhoto, db)
    
    async def get_pet_photos(
        self,
        pet_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PetPhoto]:
        """
        Get all photos for a pet.
        
        Args:
            pet_id: UUID of the pet.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of pet photos.
        """
        query = (
            select(PetPhoto)
            .where(PetPhoto.pet_id == pet_id)
            .order_by(PetPhoto.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
