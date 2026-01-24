"""Report schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    """Schema for creating a report."""
    target_type: str = Field(..., pattern="^(pet|advertisement|profile)$")
    target_id: int
    reported_user_id: Optional[UUID] = None
    reason: str = Field(..., min_length=10, max_length=1000)


class Report(BaseModel):
    """Report response schema."""
    id: int
    reporter_id: UUID
    target_type: str
    target_id: int
    reported_user_id: Optional[UUID] = None
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True
