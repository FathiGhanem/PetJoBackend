"""Breeding request service for business logic."""
from typing import List, Optional, Tuple
from uuid import UUID

from repositories.breeding_request_repository import BreedingRequestRepository
from services.base import BaseService


class BreedingRequestService(BaseService[None, BreedingRequestRepository]):
    """Service for BreedingRequest business logic."""
    
    async def get_request_with_details(self, request_id: int):
        """Get breeding request with all related information."""
        return await self.repository.get_with_relations(request_id)
    
    async def get_user_requests(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all breeding requests belonging to a user."""
        return await self.repository.get_by_owner(owner_id, skip, limit)
    
    async def get_pet_requests(self, pet_id: UUID):
        """Get all breeding requests for a specific pet."""
        return await self.repository.get_by_pet(pet_id)
    
    async def get_active_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        city_id: Optional[int] = None
    ):
        """Get all active breeding requests with optional filters."""
        return await self.repository.get_active_requests(
            skip, limit, category_id, city_id
        )
    
    async def find_matches(
        self,
        request_id: int,
        skip: int = 0,
        limit: int = 20
    ):
        """
        Find potential breeding matches for a request.
        Returns list of compatible breeding requests.
        """
        return await self.repository.find_potential_matches(
            request_id, skip, limit
        )
    
    async def search_requests(
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
            Tuple of (list of requests, total count).
        """
        return await self.repository.search_requests(filters, skip, limit)
    
    async def verify_owner(self, request_id: int, user_id: UUID) -> bool:
        """Verify if user is the owner of the breeding request."""
        request = await self.repository.get_by_id(request_id)
        if not request:
            return False
        return str(request.owner_id) == str(user_id)
    
    async def update_status(
        self,
        request_id: int,
        status: str,
        user_id: UUID
    ) -> Optional[any]:
        """
        Update the status of a breeding request.
        Only owner can update.
        """
        if not await self.verify_owner(request_id, user_id):
            return None
        
        return await self.repository.update_status(request_id, status)
    
    async def cancel_request(self, request_id: int, user_id: UUID) -> Optional[any]:
        """Cancel a breeding request. Only owner can cancel."""
        return await self.update_status(request_id, "cancelled", user_id)
    
    async def mark_as_matched(self, request_id: int, user_id: UUID) -> Optional[any]:
        """Mark request as matched (found a mate). Only owner can update."""
        return await self.update_status(request_id, "matched", user_id)
    
    async def mark_as_completed(self, request_id: int, user_id: UUID) -> Optional[any]:
        """Mark request as completed (breeding done). Only owner can update."""
        return await self.update_status(request_id, "completed", user_id)
    
    async def expire_old_requests(self) -> int:
        """
        Find and expire old active requests.
        Returns count of expired requests.
        """
        expired = await self.repository.get_expired_requests()
        count = 0
        
        for request in expired:
            await self.repository.update_status(request.id, "cancelled")
            count += 1
        
        return count
