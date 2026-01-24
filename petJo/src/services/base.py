from typing import Generic, TypeVar, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepositoryType]):
    """Base service with common business logic."""
    
    def __init__(self, repository: RepositoryType):
        self.repository = repository
    
    async def get(self, id: int):
        """Get a single record by ID."""
        return await self.repository.get_by_id(id)
    
    async def get_by_id(self, id: int):
        """Alias for get() method."""
        return await self.get(id)
    
    async def list(self, skip: int = 0, limit: int = 100, filters: Optional[dict] = None):
        """List records with pagination."""
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)
    
    async def count(self, filters: Optional[dict] = None) -> int:
        """Count records."""
        return await self.repository.count(filters=filters)
    
    async def create(self, data: dict):
        """Create a new record."""
        return await self.repository.create(data)
    
    async def update(self, id: int, data: dict):
        """Update a record."""
        return await self.repository.update(id, data)
    
    async def delete(self, id: int) -> bool:
        """Delete a record."""
        return await self.repository.delete(id)
    
    async def soft_delete(self, id: int):
        """Soft delete a record."""
        return await self.repository.soft_delete(id)
    
    async def exists(self, id: int) -> bool:
        """Check if record exists."""
        return await self.repository.exists(id)
