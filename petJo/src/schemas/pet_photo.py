"""Pet photo schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PetPhotoCreate(BaseModel):
    """Schema for creating a pet photo."""
    url: str = Field(..., max_length=500)


class PetPhoto(BaseModel):
    """Pet photo response schema."""
    id: int
    pet_id: UUID
    url: str
    created_at: datetime
    
    class Config:
        from_attributes = True
