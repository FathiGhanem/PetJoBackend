from sqlalchemy import Column, BigInteger, Text
from sqlalchemy.orm import relationship

from db.base_class import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)

    # Relationships
    pets = relationship("Pet", back_populates="city")
