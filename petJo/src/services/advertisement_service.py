"""Service layer for advertisement business logic."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.advertisement import Advertisement
from repositories.advertisement_repository import AdvertisementRepository
from services.base import BaseService
from exceptions import NotFoundException, ForbiddenException


class AdvertisementService(BaseService[Advertisement, AdvertisementRepository]):
    """Service for advertisement business logic."""
    
    def __init__(self, db: AsyncSession):
        repository = AdvertisementRepository()
        repository.db = db
        super().__init__(repository)
        self.db = db
    
    async def create_advertisement(
        self,
        user_id: UUID,
        title: str,
        description: str,
        contact_phone: Optional[str] = None
    ) -> Advertisement:
        """Create a new advertisement request."""
        ad_data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "contact_phone": contact_phone
        }
        return await self.repository.create(ad_data)
    
    async def get_user_advertisements(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Get all advertisements by a user."""
        return await self.repository.get_by_user_id(user_id, skip, limit)
    
    async def get_all_advertisements(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Get all advertisements (admin only)."""
        return await self.repository.get_all(skip=skip, limit=limit)
    
    async def get_all_with_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[tuple]:
        """Get all advertisements with user details (admin only)."""
        return await self.repository.get_all_with_user(skip, limit)
    
    async def get_advertisement_by_id(self, ad_id: int) -> Advertisement:
        """Get advertisement by ID."""
        ad = await self.repository.get_by_id(ad_id)
        if not ad:
            raise NotFoundException(f"Advertisement with id {ad_id} not found")
        return ad
    
    async def update_advertisement(
        self,
        ad_id: int,
        user_id: UUID,
        update_data: dict
    ) -> Advertisement:
        """Update an advertisement (only by owner)."""
        ad = await self.get_advertisement_by_id(ad_id)
        
        # Check ownership
        if ad.user_id != user_id:
            raise ForbiddenException("You can only update your own advertisements")
        
        return await self.repository.update(ad_id, update_data)
    
    async def delete_advertisement(
        self,
        ad_id: int,
        user_id: UUID,
        is_admin: bool = False
    ) -> bool:
        """Delete an advertisement (owner or admin)."""
        ad = await self.get_advertisement_by_id(ad_id)
        
        # Check ownership or admin
        if not is_admin and ad.user_id != user_id:
            raise ForbiddenException("You can only delete your own advertisements")
        
        return await self.repository.delete(ad_id)
    
    async def count_user_advertisements(self, user_id: UUID) -> int:
        """Count advertisements by user."""
        return await self.repository.count_by_user(user_id)
    
    async def search_advertisements(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Search advertisements with optional status filter."""
        return await self.repository.search(search_term, status, skip, limit)
    
    async def count_all(self) -> int:
        """Count all advertisements."""
        return await self.repository.count()
    
    async def get_pending_advertisements(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Advertisement]:
        """Get pending advertisements (admin only)."""
        return await self.repository.get_by_status("pending", skip, limit)
    
    async def count_pending(self) -> int:
        """Count pending advertisements."""
        return await self.repository.get_pending_count()
    
    async def review_advertisement(
        self,
        ad_id: int,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Advertisement:
        """Review advertisement - approve or reject (admin only)."""
        ad = await self.get_advertisement_by_id(ad_id)
        
        update_data = {
            "status": status,
            "admin_notes": admin_notes,
            "reviewed_at": datetime.utcnow()
        }
        
        return await self.repository.update(ad_id, update_data)
