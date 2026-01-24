"""City schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class CityBase(BaseModel):
    """Base city schema."""
    name: str = Field(..., min_length=1, max_length=100)


class CityCreate(CityBase):
    """Schema for creating a city."""
    pass


class CityUpdate(BaseModel):
    """Schema for updating a city."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class City(CityBase):
    """City response schema."""
    id: int
    
    class Config:
        from_attributes = True
