"""Pet help request schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PetHelpRequestBase(BaseModel):
    """Base pet help request schema."""
    description: str = Field(..., min_length=10, max_length=1000)
    photo_url: Optional[str] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    location_address: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)


class PetHelpRequestCreate(PetHelpRequestBase):
    """Schema for creating a pet help request."""
    pass


class PetHelpRequestUpdate(BaseModel):
    """Schema for updating a pet help request."""
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    photo_url: Optional[str] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    location_address: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)


class PetHelpRequest(PetHelpRequestBase):
    """Pet help request response schema."""
    id: int
    owner_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PetHelpRequestPublic(BaseModel):
    """Public pet help request schema (without owner details)."""
    id: int
    description: str
    photo_url: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    phone_number: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
