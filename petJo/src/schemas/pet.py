from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from utils.validators import validate_age, validate_phone_number
from core.sanitize import sanitize_text


class PetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Pet name")
    breed: Optional[str] = Field(None, max_length=100, description="Breed")
    age: Optional[int] = Field(None, ge=0, le=50, description="Age in years")
    gender: Optional[str] = Field(None, max_length=20, description="Gender")
    vaccinated: bool = Field(default=False, description="Vaccination status")
    spayed: bool = Field(default=False, description="Spayed/neutered status")
    description: Optional[str] = Field(None, max_length=2000, description="Description")
    city_id: Optional[int] = Field(None, description="City ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    main_photo_url: Optional[str] = Field(None, description="Main photo URL")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    status: str = Field(default="available", description="Pet status")
    visibility: str = Field(default="public", description="Visibility")
    
    @field_validator('age')
    @classmethod
    def validate_age_range(cls, v):
        if v is not None and not validate_age(v):
            raise ValueError('Age must be between 0 and 50')
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if v and not validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('name', 'breed', 'gender', 'description')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        return sanitize_text(v)


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    breed: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=50)
    gender: Optional[str] = Field(None, max_length=20)
    vaccinated: Optional[bool] = None
    spayed: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=2000)
    city_id: Optional[int] = None
    category_id: Optional[int] = None
    main_photo_url: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class Pet(PetBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PetPublic(BaseModel):
    """Public pet information (without sensitive data)."""
    id: UUID
    name: str
    breed: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    description: Optional[str]
    main_photo_url: Optional[str]
    status: str
    city_id: Optional[int]
    category_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PetWithOwner(Pet):
    owner: "ProfilePublic"
    
    model_config = ConfigDict(from_attributes=True)


from schemas.user import ProfilePublic
PetWithOwner.model_rebuild()
