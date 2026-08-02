from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    variant_id = Column(
        Integer,
        ForeignKey(
            "product_variants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    # Manufactured Stock
    k_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Ready-made Stock
    r_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    minimum_stock = Column(
        Integer,
        default=0,
    )

    maximum_stock = Column(
        Integer,
        default=0,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    variant = relationship(
        "ProductVariant",
        back_populates="stock",
    )

    @property
    def quantity(self):
        return self.k_stock + self.r_stock