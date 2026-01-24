from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from db.base_class import Base


class PetStatus(str, enum.Enum):
    AVAILABLE = "available"
    ADOPTED = "adopted"
    LOST = "lost"
    FOUND = "found"
    HELP = "help"


class PetVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = (
        Index('idx_pet_status', 'status'),
        Index('idx_pet_visibility', 'visibility'),
        Index('idx_pet_owner', 'owner_id'),
        Index('idx_pet_city', 'city_id'),
        Index('idx_pet_category', 'category_id'),
        Index('idx_pet_deleted', 'deleted_at'),
        Index('idx_pet_created', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    category_id = Column(BigInteger, ForeignKey("categories.id"), nullable=True, index=True)
    breed = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(Text, nullable=True)
    vaccinated = Column(Boolean, default=False)
    spayed = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    city_id = Column(BigInteger, ForeignKey("cities.id"), nullable=True, index=True)
    main_photo_url = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="available", index=True)
    visibility = Column(Text, nullable=False, default="public", index=True)
    phone_number = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    owner = relationship("User", back_populates="pets")
    category = relationship("Category", back_populates="pets")
    city = relationship("City", back_populates="pets")
    photos = relationship("PetPhoto", back_populates="pet", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="pet", cascade="all, delete-orphan")
