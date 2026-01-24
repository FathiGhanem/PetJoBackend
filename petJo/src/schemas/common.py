"""Common response models."""

from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""
    
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = False
    error: dict
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Simple message response."""
    
    success: bool = True
    message: str
