"""Pet repository for database operations."""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.pet import Pet
from repositories.base import BaseRepository


class PetRepository(BaseRepository[Pet]):
    """Repository for Pet model with specific queries."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Pet, db)
    
    async def get_by_owner(
        self, 
        owner_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Pet]:
        """Get all pets by owner ID."""
        result = await self.db.execute(
            select(Pet)
            .where(Pet.owner_id == owner_id)
            .where(Pet.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_with_relations(self, pet_id: UUID) -> Optional[Pet]:
        """Get pet with owner, category, city, and photos."""
        result = await self.db.execute(
            select(Pet)
            .options(
                selectinload(Pet.owner),
                selectinload(Pet.category),
                selectinload(Pet.city),
                selectinload(Pet.photos)
            )
            .where(Pet.id == pet_id)
            .where(Pet.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    
    async def get_available_pets(
        self,
        skip: int = 0,
        limit: int = 100,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> List[Pet]:
        """Get available pets with filters."""
        query = select(Pet).where(
            Pet.status == "available",
            Pet.visibility == "public",
            Pet.deleted_at.is_(None)
        )
        
        if city_id:
            query = query.where(Pet.city_id == city_id)
        if category_id:
            query = query.where(Pet.category_id == category_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_pets(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Pet]:
        """Search pets by name or breed."""
        result = await self.db.execute(
            select(Pet)
            .where(Pet.deleted_at.is_(None))
            .where(
                (Pet.name.ilike(f"%{search_term}%")) |
                (Pet.breed.ilike(f"%{search_term}%"))
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def advanced_search(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Pet], int]:
        """
        Perform advanced search with multiple filters.
        
        Args:
            filters: Dictionary of filter criteria (search_term, category_id, etc.)
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            Tuple of (list of pets, total count).
        """
        # Base query - only non-deleted pets
        query = select(Pet).where(Pet.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Pet).where(Pet.deleted_at.is_(None))
        
        # Text search
        if filters.get("search_term"):
            search_term = filters["search_term"]
            search_condition = or_(
                Pet.name.ilike(f"%{search_term}%"),
                Pet.breed.ilike(f"%{search_term}%"),
                Pet.description.ilike(f"%{search_term}%")
            )
            query = query.where(search_condition)
            count_query = count_query.where(search_condition)
        
        # Category filter
        if filters.get("category_id"):
            query = query.where(Pet.category_id == filters["category_id"])
            count_query = count_query.where(Pet.category_id == filters["category_id"])
        
        # City filter
        if filters.get("city_id"):
            query = query.where(Pet.city_id == filters["city_id"])
            count_query = count_query.where(Pet.city_id == filters["city_id"])
        
        # Status filter
        if filters.get("status"):
            query = query.where(Pet.status == filters["status"])
            count_query = count_query.where(Pet.status == filters["status"])
        else:
            # Default: only show public available pets
            query = query.where(Pet.visibility == "public")
            count_query = count_query.where(Pet.visibility == "public")
        
        # Gender filter
        if filters.get("gender"):
            query = query.where(Pet.gender.ilike(filters["gender"]))
            count_query = count_query.where(Pet.gender.ilike(filters["gender"]))
        
        # Age range filters
        if filters.get("min_age") is not None:
            query = query.where(Pet.age >= filters["min_age"])
            count_query = count_query.where(Pet.age >= filters["min_age"])
        
        if filters.get("max_age") is not None:
            query = query.where(Pet.age <= filters["max_age"])
            count_query = count_query.where(Pet.age <= filters["max_age"])
        
        # Vaccinated filter
        if filters.get("vaccinated") is not None:
            query = query.where(Pet.vaccinated == filters["vaccinated"])
            count_query = count_query.where(Pet.vaccinated == filters["vaccinated"])
        
        # Spayed filter
        if filters.get("spayed") is not None:
            query = query.where(Pet.spayed == filters["spayed"])
            count_query = count_query.where(Pet.spayed == filters["spayed"])
        
        # Get total count
        total = await self.db.scalar(count_query)
        
        # Add ordering and pagination
        query = query.order_by(Pet.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        pets = result.scalars().all()
        
        return pets, total or 0
