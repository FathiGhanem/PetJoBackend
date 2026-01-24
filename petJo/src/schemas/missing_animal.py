"""Pydantic schemas for missing animal reports."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID

from core.sanitize import sanitize_text


class MissingAnimalBase(BaseModel):
    """Base schema for missing animal."""
    pet_name: str = Field(..., min_length=1, max_length=100, description="Name of the missing animal")
    animal_type: Optional[str] = Field(None, max_length=50, description="Type of animal (dog, cat, bird, etc.)")
    breed: Optional[str] = Field(None, max_length=100, description="Breed")
    color: Optional[str] = Field(None, max_length=100, description="Color or markings")
    size: Optional[str] = Field(None, pattern="^(small|medium|large)$", description="Size: small, medium, large")
    age_approximate: Optional[int] = Field(None, ge=0, le=50, description="Approximate age in years")
    gender: Optional[str] = Field(None, max_length=20, description="Gender")
    
    distinguishing_features: Optional[str] = Field(None, max_length=2000, description="Unique identifying features")
    microchip_id: Optional[str] = Field(None, max_length=50, description="Microchip ID if available")
    collar_description: Optional[str] = Field(None, max_length=200, description="Collar description")
    
    last_seen_location: str = Field(..., max_length=500, description="Where the animal was last seen")
    last_seen_date: datetime = Field(..., description="When the animal was last seen")
    city_id: Optional[int] = Field(None, description="City ID")
    
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    
    reward_offered: bool = Field(default=False, description="Is a reward offered")
    reward_amount: Optional[str] = Field(None, max_length=50, description="Reward amount or description")
    
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    
    description: Optional[str] = Field(None, max_length=2000, description="Additional description")
    
    @field_validator('pet_name', 'breed', 'color', 'distinguishing_features', 'collar_description', 'last_seen_location', 'description', 'reward_amount')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        return sanitize_text(v)
    
    @field_validator('animal_type')
    @classmethod
    def normalize_animal_type(cls, v):
        """Normalize animal type to lowercase."""
        if v:
            return sanitize_text(v.lower())
        return v


class MissingAnimalCreate(MissingAnimalBase):
    """Schema for creating a missing animal report."""
    pet_id: Optional[UUID] = Field(None, description="ID of registered pet (optional)")
    photo_urls: Optional[str] = Field(None, description="Comma-separated photo URLs")


class MissingAnimalUpdate(BaseModel):
    """Schema for updating a missing animal report."""
    pet_name: Optional[str] = Field(None, min_length=1, max_length=100)
    animal_type: Optional[str] = Field(None, max_length=50)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, pattern="^(small|medium|large)$")
    age_approximate: Optional[int] = Field(None, ge=0, le=50)
    gender: Optional[str] = Field(None, max_length=20)
    
    distinguishing_features: Optional[str] = Field(None, max_length=2000)
    microchip_id: Optional[str] = Field(None, max_length=50)
    collar_description: Optional[str] = Field(None, max_length=200)
    
    last_seen_location: Optional[str] = Field(None, max_length=500)
    last_seen_date: Optional[datetime] = None
    city_id: Optional[int] = None
    
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    reward_offered: Optional[bool] = None
    reward_amount: Optional[str] = Field(None, max_length=50)
    
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=255)
    
    description: Optional[str] = Field(None, max_length=2000)
    photo_urls: Optional[str] = None
    
    @field_validator('pet_name', 'breed', 'color', 'distinguishing_features', 'collar_description', 'last_seen_location', 'description', 'reward_amount')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        return sanitize_text(v)
    
    @field_validator('animal_type')
    @classmethod
    def normalize_animal_type(cls, v):
        """Normalize animal type to lowercase."""
        if v:
            return sanitize_text(v.lower())
        return v


class MissingAnimalStatusUpdate(BaseModel):
    """Schema for updating missing animal status."""
    status: str = Field(..., pattern="^(missing|sighted|found|reunited|closed)$", description="New status")


class MissingAnimalPublic(BaseModel):
    """Public schema for missing animal (response)."""
    id: int
    pet_id: Optional[UUID]
    owner_id: UUID
    status: str
    
    pet_name: str
    animal_type: Optional[str]
    breed: Optional[str]
    color: Optional[str]
    size: Optional[str]
    age_approximate: Optional[int]
    gender: Optional[str]
    
    distinguishing_features: Optional[str]
    microchip_id: Optional[str]
    collar_description: Optional[str]
    
    last_seen_location: str
    last_seen_date: datetime
    city_id: Optional[int]
    
    latitude: Optional[float]
    longitude: Optional[float]
    
    reward_offered: bool
    reward_amount: Optional[str]
    
    contact_phone: Optional[str]
    contact_email: Optional[str]
    
    description: Optional[str]
    photo_urls: Optional[str]
    
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    found_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class MissingAnimalWithRelations(MissingAnimalPublic):
    """Missing animal with related data."""
    # Can be extended with city, pet, owner details if needed
    pass
