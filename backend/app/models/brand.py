from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    brand_name = Column(
        String(150),
        unique=True,
    )

    products = relationship(
        "Product",
        back_populates="brand",
    )