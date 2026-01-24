"""Hero section schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HeroBase(BaseModel):
    """Base hero schema."""
    img_path: Optional[str] = Field(None, max_length=500)
    link: Optional[str] = Field(None, max_length=500)


class HeroCreate(HeroBase):
    """Schema for creating a hero."""
    img_path: str = Field(..., max_length=500)


class HeroUpdate(BaseModel):
    """Schema for updating a hero."""
    img_path: Optional[str] = Field(None, max_length=500)
    link: Optional[str] = Field(None, max_length=500)


class Hero(HeroBase):
    """Hero response schema."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
