"""Pet service for business logic."""
from typing import List, Optional, Tuple
from uuid import UUID

from repositories.pet_repository import PetRepository
from services.base import BaseService


class PetService(BaseService[None, PetRepository]):
    """Service for Pet business logic."""
    
    async def get_pet_with_details(self, pet_id: UUID):
        """Get pet with all related information."""
        return await self.repository.get_with_relations(pet_id)
    
    async def get_user_pets(
        self, 
        owner_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ):
        """Get all pets belonging to a user."""
        return await self.repository.get_by_owner(owner_id, skip, limit)
    
    async def search_available_pets(
        self,
        skip: int = 0,
        limit: int = 100,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        search_term: Optional[str] = None
    ):
        """Search and filter available pets."""
        if search_term:
            return await self.repository.search_pets(search_term, skip, limit)
        
        return await self.repository.get_available_pets(
            skip, limit, city_id, category_id
        )
    
    async def verify_owner(self, pet_id: UUID, user_id: UUID) -> bool:
        """Verify if user is the owner of the pet."""
        pet = await self.repository.get_by_id(pet_id)
        if not pet:
            return False
        return str(pet.owner_id) == str(user_id)
    
    async def publish_pet(self, pet_id: UUID, user_id: UUID) -> Optional[any]:
        """Make a pet listing public."""
        if not await self.verify_owner(pet_id, user_id):
            return None
        
        return await self.repository.update(pet_id, {"visibility": "public"})
    
    async def unpublish_pet(self, pet_id: UUID, user_id: UUID) -> Optional[any]:
        """Make a pet listing private."""
        if not await self.verify_owner(pet_id, user_id):
            return None
        
        return await self.repository.update(pet_id, {"visibility": "private"})
    
    async def advanced_search(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List, int]:
        """
        Perform advanced search with multiple filters.
        
        Args:
            filters: Dictionary of filter criteria.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            Tuple of (list of pets, total count).
        """
        return await self.repository.advanced_search(filters, skip, limit)
