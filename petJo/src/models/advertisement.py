from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from db.base_class import Base


class Advertisement(Base):
    __tablename__ = "advertisements"
    __table_args__ = (
        Index('idx_advertisement_user', 'user_id'),
        Index('idx_advertisement_status', 'status'),
        Index('idx_advertisement_created', 'created_at'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    contact_phone = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="pending", index=True)  # pending, approved, rejected
    admin_notes = Column(Text, nullable=True)  # Admin feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="advertisements")
