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

    # ==========================================================
    # STOCK QUANTITIES
    # ==========================================================

    # Manufactured / K Stock
    k_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Ready-made / R Stock
    r_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ==========================================================
    # STOCK THRESHOLDS
    # ==========================================================

    # Minimum TOTAL stock
    minimum_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Minimum K stock
    k_minimum_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Minimum R stock
    r_minimum_stock = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Maximum TOTAL stock
    maximum_stock = Column(
        Integer,
        nullable=False,
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

    # ==========================================================
    # TOTAL QUANTITY
    # ==========================================================

    @property
    def quantity(self):
        return self.k_stock + self.r_stock