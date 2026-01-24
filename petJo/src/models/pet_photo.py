from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.base_class import Base


class PetPhoto(Base):
    __tablename__ = "pet_photos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pet = relationship("Pet", back_populates="photos")
