"""Breeding request repository for database operations."""
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.breeding_request import BreedingRequest
from repositories.base import BaseRepository


class BreedingRequestRepository(BaseRepository[BreedingRequest]):
    """Repository for BreedingRequest model with specific queries."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BreedingRequest, db)
    
    async def get_by_owner(
        self, 
        owner_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[BreedingRequest]:
        """Get all breeding requests by owner ID."""
        result = await self.db.execute(
            select(BreedingRequest)
            .where(BreedingRequest.owner_id == owner_id)
            .order_by(BreedingRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_pet(self, pet_id: UUID) -> List[BreedingRequest]:
        """Get all breeding requests for a specific pet."""
        result = await self.db.execute(
            select(BreedingRequest)
            .where(BreedingRequest.pet_id == pet_id)
            .order_by(BreedingRequest.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_with_relations(self, request_id: int) -> Optional[BreedingRequest]:
        """Get breeding request with pet, owner, category, and city."""
        result = await self.db.execute(
            select(BreedingRequest)
            .options(
                selectinload(BreedingRequest.pet),
                selectinload(BreedingRequest.owner),
                selectinload(BreedingRequest.category),
                selectinload(BreedingRequest.city)
            )
            .where(BreedingRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_requests(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        city_id: Optional[int] = None
    ) -> List[BreedingRequest]:
        """Get all active breeding requests with optional filters."""
        query = select(BreedingRequest).where(
            BreedingRequest.status == "active"
        )
        
        if category_id:
            query = query.where(BreedingRequest.category_id == category_id)
        if city_id:
            query = query.where(BreedingRequest.city_id == city_id)
        
        query = query.order_by(BreedingRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def find_potential_matches(
        self,
        request_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[BreedingRequest]:
        """
        Find potential breeding matches for a request.
        Matches based on: category, city, breed, age range.
        """
        # Get the original request
        original = await self.get_by_id(request_id)
        if not original:
            return []
        
        # Build query for matching
        query = select(BreedingRequest).where(
            and_(
                BreedingRequest.id != request_id,  # Not the same request
                BreedingRequest.status == "active",  # Active only
                BreedingRequest.owner_id != original.owner_id,  # Different owner
                BreedingRequest.category_id == original.category_id  # Same category
            )
        )
        
        # Add optional filters
        if original.city_id:
            query = query.where(BreedingRequest.city_id == original.city_id)
        
        if original.preferred_breed:
            query = query.where(
                BreedingRequest.preferred_breed.ilike(f"%{original.preferred_breed}%")
            )
        
        query = query.order_by(BreedingRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_requests(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[BreedingRequest], int]:
        """
        Advanced search for breeding requests with multiple filters.
        
        Supported filters:
        - category_id: Filter by pet category
        - city_id: Filter by location
        - status: Filter by request status
        - is_pedigree: Filter pedigree pets
        - has_papers: Filter pets with papers
        - health_certified: Filter health certified pets
        - search_term: Search in title, description, breed
        """
        query = select(BreedingRequest)
        count_query = select(func.count()).select_from(BreedingRequest)
        
        # Apply filters
        conditions = []
        
        if filters.get("category_id"):
            conditions.append(BreedingRequest.category_id == filters["category_id"])
        
        if filters.get("city_id"):
            conditions.append(BreedingRequest.city_id == filters["city_id"])
        
        if filters.get("status"):
            conditions.append(BreedingRequest.status == filters["status"])
        else:
            # Default to active only
            conditions.append(BreedingRequest.status == "active")
        
        if filters.get("is_pedigree") is not None:
            conditions.append(BreedingRequest.is_pedigree == filters["is_pedigree"])
        
        if filters.get("has_papers") is not None:
            conditions.append(BreedingRequest.has_papers == filters["has_papers"])
        
        if filters.get("health_certified") is not None:
            conditions.append(BreedingRequest.health_certified == filters["health_certified"])
        
        if filters.get("search_term"):
            search_term = filters["search_term"]
            conditions.append(
                or_(
                    BreedingRequest.title.ilike(f"%{search_term}%"),
                    BreedingRequest.description.ilike(f"%{search_term}%"),
                    BreedingRequest.preferred_breed.ilike(f"%{search_term}%")
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get results
        query = query.order_by(BreedingRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return requests, total
    
    async def update_status(
        self,
        request_id: int,
        status: str
    ) -> Optional[BreedingRequest]:
        """Update the status of a breeding request."""
        return await self.update(request_id, {"status": status, "updated_at": datetime.utcnow()})
    
    async def get_expired_requests(self) -> List[BreedingRequest]:
        """Get all expired active requests."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(BreedingRequest).where(
                and_(
                    BreedingRequest.status == "active",
                    BreedingRequest.expires_at.isnot(None),
                    BreedingRequest.expires_at < now
                )
            )
        )
        return result.scalars().all()
