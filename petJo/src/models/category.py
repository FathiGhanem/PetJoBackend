from sqlalchemy import Column, BigInteger, Text
from sqlalchemy.orm import relationship

from db.base_class import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    # Relationships
    pets = relationship("Pet", back_populates="category")
