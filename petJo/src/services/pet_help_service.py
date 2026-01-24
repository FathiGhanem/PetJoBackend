"""Pet help request service for business logic."""
from typing import List, Optional
from uuid import UUID

from repositories.pet_help_repository import PetHelpRequestRepository
from services.base import BaseService


class PetHelpRequestService(BaseService[None, PetHelpRequestRepository]):
    """Service for PetHelpRequest business logic."""
    
    async def get_help_request_with_details(self, help_id: int):
        """
        Get help request with all related information.
        
        Args:
            help_id: ID of the help request.
            
        Returns:
            PetHelpRequest with relationships loaded.
        """
        return await self.repository.get_with_requester(help_id)
    
    async def get_user_help_requests(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ):
        """
        Get all help requests belonging to a user.
        
        Args:
            owner_id: UUID of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of user's help requests.
        """
        return await self.repository.get_by_owner(owner_id, skip, limit)
    
    async def get_all_public_requests(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        """
        Get all public help requests.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of all help requests.
        """
        return await self.repository.get_all_public(skip, limit)
    
    async def search_by_location(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 100
    ):
        """
        Search help requests by location.
        
        Args:
            lat: Latitude of search center.
            lng: Longitude of search center.
            radius_km: Search radius in kilometers.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of help requests within radius.
        """
        return await self.repository.search_by_location(
            lat, lng, radius_km, skip, limit
        )
    
    async def verify_owner(self, help_id: int, user_id: UUID) -> bool:
        """
        Verify if user is the owner of the help request.
        
        Args:
            help_id: ID of the help request.
            user_id: UUID of the user.
            
        Returns:
            True if user is owner, False otherwise.
        """
        help_request = await self.repository.get_by_id(help_id)
        if not help_request:
            return False
        return str(help_request.owner_id) == str(user_id)
