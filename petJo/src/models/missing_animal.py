"""Missing animal model for lost/found pet reports."""
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Float, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from db.base_class import Base


class MissingAnimal(Base):
    """Model for missing/lost animal reports."""
    
    __tablename__ = "missing_animals"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # Optional link to registered pet
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Owner information
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Status: missing, sighted, found, reunited, closed
    status = Column(String(20), nullable=False, default="missing", index=True)
    
    # Animal details (for non-registered pets or additional info)
    pet_name = Column(String(100), nullable=False)
    animal_type = Column(String(50), nullable=True)  # dog, cat, bird, etc.
    breed = Column(String(100), nullable=True)
    color = Column(String(100), nullable=True)
    size = Column(String(20), nullable=True)  # small, medium, large
    age_approximate = Column(Integer, nullable=True)  # in years
    gender = Column(String(20), nullable=True)
    
    # Distinguishing features
    distinguishing_features = Column(Text, nullable=True)
    microchip_id = Column(String(50), nullable=True)
    collar_description = Column(String(200), nullable=True)
    
    # Location information
    last_seen_location = Column(String(500), nullable=False)
    last_seen_date = Column(DateTime(timezone=True), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True, index=True)
    
    # Optional GPS coordinates for map display
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Reward
    reward_offered = Column(Boolean, default=False)
    reward_amount = Column(String(50), nullable=True)  # e.g., "$500" or "Reward"
    
    # Contact information
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Additional details
    description = Column(Text, nullable=True)
    
    # Photos (comma-separated URLs or JSON array in future)
    photo_urls = Column(Text, nullable=True)
    
    # Visibility
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    found_at = Column(DateTime(timezone=True), nullable=True)  # When marked as found
    
    # Relationships
    owner = relationship("User", back_populates="missing_animals", foreign_keys=[owner_id])
    pet = relationship("Pet", backref="missing_reports", foreign_keys=[pet_id])
    city = relationship("City", backref="missing_animals", foreign_keys=[city_id])
    
    def __repr__(self):
        return f"<MissingAnimal(id={self.id}, pet_name='{self.pet_name}', status='{self.status}')>"
