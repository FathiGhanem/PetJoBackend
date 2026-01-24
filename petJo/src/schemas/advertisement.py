"""Advertisement schemas for request/response validation."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from core.sanitize import sanitize_text


class AdvertisementBase(BaseModel):
    """Base advertisement schema."""
    title: str = Field(..., min_length=5, max_length=200, description="Advertisement title")
    description: str = Field(..., min_length=10, max_length=2000, description="Advertisement description")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")


class AdvertisementCreate(AdvertisementBase):
    """Schema for creating an advertisement request."""
    
    @field_validator('title', 'description')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        if v:
            return sanitize_text(v)
        return v
    
    @field_validator('contact_phone')
    @classmethod
    def validate_phone(cls, v):
        """Basic phone validation."""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class AdvertisementUpdate(BaseModel):
    """Schema for updating an advertisement."""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    contact_phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('title', 'description')
    @classmethod
    def sanitize_text_fields(cls, v):
        """Sanitize text fields to prevent XSS attacks."""
        if v:
            return sanitize_text(v)
        return v


class Advertisement(AdvertisementBase):
    """Advertisement response schema."""
    id: int
    user_id: UUID
    status: str  # pending, approved, rejected
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AdvertisementWithUser(Advertisement):
    """Advertisement with user information."""
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AdvertisementReview(BaseModel):
    """Schema for admin to review advertisement."""
    status: Literal["approved", "rejected"] = Field(..., description="Approval status")
    admin_notes: Optional[str] = Field(None, max_length=500, description="Admin feedback or reason for rejection")
