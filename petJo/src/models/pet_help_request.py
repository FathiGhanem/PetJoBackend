from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.base_class import Base


class PetHelpRequest(Base):
    __tablename__ = "pet_help_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    phone_number = Column(Text, nullable=True)
    location_address = Column(Text, nullable=True)

    # Relationships
    requester = relationship("User", back_populates="help_requests")
