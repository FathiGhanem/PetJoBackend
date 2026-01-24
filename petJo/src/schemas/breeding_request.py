"""Pydantic schemas for breeding requests."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from core.sanitize import sanitize_text


class BreedingRequestBase(BaseModel):
    """Base schema for breeding request."""
    title: str = Field(..., min_length=3, max_length=200, description="Title of breeding request")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    category_id: Optional[int] = Field(None, description="Pet category ID")
    preferred_breed: Optional[str] = Field(None, max_length=100, description="Preferred breed for mating")
    city_id: Optional[int] = Field(None, description="City ID")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    is_pedigree: bool = Field(default=False, description="Is the pet a pedigree")
    has_papers: bool = Field(default=False, description="Does the pet have breeding papers")
    health_certified: bool = Field(default=False, description="Is the pet health certified")
    min_age: Optional[int] = Field(None, ge=0, le=240, description="Minimum age of mate (months)")
    max_age: Optional[int] = Field(None, ge=0, le=240, description="Maximum age of mate (months)")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    expires_at: Optional[datetime] = Field(None, description="When the request expires")
    
    @field_validator('title', 'description', 'preferred_breed', 'notes')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        return sanitize_text(v)


class BreedingRequestCreate(BreedingRequestBase):
    """Schema for creating a breeding request."""
    pet_id: UUID = Field(..., description="ID of the pet looking for a mate")


class BreedingRequestUpdate(BaseModel):
    """Schema for updating a breeding request."""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    preferred_breed: Optional[str] = Field(None, max_length=100)
    city_id: Optional[int] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    is_pedigree: Optional[bool] = None
    has_papers: Optional[bool] = None
    health_certified: Optional[bool] = None
    min_age: Optional[int] = Field(None, ge=0, le=240)
    max_age: Optional[int] = Field(None, ge=0, le=240)
    notes: Optional[str] = Field(None, max_length=1000)
    expires_at: Optional[datetime] = None


class BreedingRequestStatusUpdate(BaseModel):
    """Schema for updating breeding request status."""
    status: str = Field(..., pattern="^(active|matched|completed|cancelled)$", description="New status")


class BreedingRequest(BreedingRequestBase):
    """Schema for breeding request response."""
    id: int
    pet_id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class BreedingRequestPublic(BaseModel):
    """Public schema for breeding request (limited info)."""
    id: int
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    preferred_breed: Optional[str] = None
    city_id: Optional[int] = None
    is_pedigree: bool
    has_papers: bool
    health_certified: bool
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BreedingMatch(BaseModel):
    """Schema for potential breeding match."""
    request: BreedingRequestPublic
    compatibility_score: float = Field(..., ge=0, le=1, description="Match compatibility score")
    match_reasons: list[str] = Field(default_factory=list, description="Reasons for the match")
