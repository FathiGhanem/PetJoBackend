from sqlalchemy import Column, BigInteger, DateTime, Text
from sqlalchemy.sql import func

from db.base_class import Base


class Hero(Base):
    __tablename__ = "heroes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    img_path = Column(Text, nullable=True)
    link = Column(Text, nullable=True)
