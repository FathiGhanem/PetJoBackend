"""Filtering utilities."""

from typing import Optional
from pydantic import BaseModel, Field


class PetFilter(BaseModel):
    """Filter parameters for pets."""
    
    species: Optional[str] = Field(None, description="Filter by species")
    breed: Optional[str] = Field(None, description="Filter by breed")
    city_id: Optional[int] = Field(None, description="Filter by city")
    category_id: Optional[int] = Field(None, description="Filter by category")
    status: Optional[str] = Field(None, description="Filter by status")
    visibility: Optional[str] = Field(None, description="Filter by visibility")
    min_age: Optional[int] = Field(None, ge=0, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, description="Maximum age")
    gender: Optional[str] = Field(None, description="Filter by gender")
    vaccinated: Optional[bool] = Field(None, description="Filter by vaccination status")
    spayed: Optional[bool] = Field(None, description="Filter by spayed/neutered status")
    search: Optional[str] = Field(None, description="Search by name or breed")
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None and k != 'search'}


class SortParams(BaseModel):
    """Sorting parameters."""
    
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
