"""Pet breeding request model for finding mates."""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, Boolean, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from db.base_class import Base


class BreedingRequestStatus(str, enum.Enum):
    """Status of breeding request."""
    ACTIVE = "active"  # Looking for mate
    MATCHED = "matched"  # Found a mate
    COMPLETED = "completed"  # Breeding completed
    CANCELLED = "cancelled"  # Request cancelled


class BreedingRequest(Base):
    """Model for pet breeding/mating requests."""
    __tablename__ = "breeding_requests"
    __table_args__ = (
        Index('idx_breeding_pet', 'pet_id'),
        Index('idx_breeding_owner', 'owner_id'),
        Index('idx_breeding_status', 'status'),
        Index('idx_breeding_city', 'city_id'),
        Index('idx_breeding_category', 'category_id'),
        Index('idx_breeding_created', 'created_at'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Pet and owner information
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    status = Column(Text, nullable=False, default="active", index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # Matching criteria
    category_id = Column(BigInteger, ForeignKey("categories.id"), nullable=True, index=True)
    preferred_breed = Column(Text, nullable=True)
    city_id = Column(BigInteger, ForeignKey("cities.id"), nullable=True, index=True)
    
    # Contact and preferences
    contact_phone = Column(Text, nullable=True)
    is_pedigree = Column(Boolean, default=False)
    has_papers = Column(Boolean, default=False)
    health_certified = Column(Boolean, default=False)
    
    # Additional info
    min_age = Column(Integer, nullable=True)  # Minimum age of mate (in months)
    max_age = Column(Integer, nullable=True)  # Maximum age of mate (in months)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When request expires
    
    # Relationships
    pet = relationship("Pet", backref="breeding_requests")
    owner = relationship("User", backref="breeding_requests")
    category = relationship("Category")
    city = relationship("City")
