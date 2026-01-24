"""Favorite schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class FavoriteCreate(BaseModel):
    """Schema for creating a favorite."""
    pet_id: UUID


class Favorite(BaseModel):
    """Favorite response schema."""
    id: int
    user_id: UUID
    pet_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteWithPet(BaseModel):
    """Favorite with pet details."""
    id: int
    pet_id: UUID
    created_at: datetime
    pet: Optional["PetPublic"] = None
    
    class Config:
        from_attributes = True


from schemas.pet import PetPublic
FavoriteWithPet.model_rebuild()
