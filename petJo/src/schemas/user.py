from pydantic import BaseModel, EmailStr, ConfigDict, Field, validator
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

from utils.validators import validate_phone_number


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    city: Optional[str] = Field(None, max_length=100, description="City")
    preferences: Optional[Any] = Field(None, description="User preferences (JSON)")
    is_active: Optional[bool] = Field(True, description="Account active status")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    preferences: Optional[Any] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v


class UserInDB(UserBase):
    id: UUID
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    pass


class UserPublic(BaseModel):
    """Public user information (limited data)."""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Profile Schemas
class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    city: Optional[str] = Field(None, max_length=100, description="City")
    role: Optional[str] = Field("user", description="User role")
    preferences: Optional[Any] = Field(None, description="User preferences (JSON)")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not validate_phone_number(v):
            raise ValueError('Invalid phone number format')
        return v


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    preferences: Optional[Any] = None


class Profile(ProfileBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProfilePublic(BaseModel):
    """Public profile information."""
    id: UUID
    full_name: Optional[str]
    avatar_url: Optional[str]
    city: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
