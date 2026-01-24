"""Pet help request repository for database operations."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.pet_help_request import PetHelpRequest
from repositories.base import BaseRepository


class PetHelpRequestRepository(BaseRepository[PetHelpRequest]):
    """Repository for PetHelpRequest model with specific queries."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(PetHelpRequest, db)
    
    async def get_by_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PetHelpRequest]:
        """
        Get all help requests by owner ID.
        
        Args:
            owner_id: UUID of the owner.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of pet help requests.
        """
        result = await self.db.execute(
            select(PetHelpRequest)
            .where(PetHelpRequest.owner_id == owner_id)
            .order_by(desc(PetHelpRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_with_requester(self, help_id: int) -> Optional[PetHelpRequest]:
        """
        Get help request with requester details.
        
        Args:
            help_id: ID of the help request.
            
        Returns:
            PetHelpRequest with relationships loaded, or None.
        """
        result = await self.db.execute(
            select(PetHelpRequest)
            .options(selectinload(PetHelpRequest.requester))
            .where(PetHelpRequest.id == help_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_public(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[PetHelpRequest]:
        """
        Get all public help requests.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of all pet help requests ordered by creation date.
        """
        result = await self.db.execute(
            select(PetHelpRequest)
            .order_by(desc(PetHelpRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_by_location(
        self,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[PetHelpRequest]:
        """
        Search help requests by location within a radius.
        
        Uses Haversine formula approximation for distance calculation.
        
        Args:
            lat: Latitude of search center.
            lng: Longitude of search center.
            radius_km: Search radius in kilometers.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of help requests within the radius.
        """
        # Simple bounding box filter (for better performance with indexes)
        # Approximate: 1 degree latitude ≈ 111 km
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * abs(lat))  # Adjust for latitude
        
        result = await self.db.execute(
            select(PetHelpRequest)
            .where(
                PetHelpRequest.location_lat.isnot(None),
                PetHelpRequest.location_lng.isnot(None),
                PetHelpRequest.location_lat.between(lat - lat_delta, lat + lat_delta),
                PetHelpRequest.location_lng.between(lng - lng_delta, lng + lng_delta)
            )
            .order_by(desc(PetHelpRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
