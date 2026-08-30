from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sale_id = Column(
        Integer,
        ForeignKey(
            "sales.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    variant_id = Column(
        Integer,
        ForeignKey(
            "product_variants.id",
        ),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
    )

    # ------------------------------------------------------
    # Stock Source
    # ------------------------------------------------------

    stock_type = Column(
        String(20),
        nullable=False,
        default="MIXED",
    )

    k_quantity = Column(
        Integer,
        default=0,
        nullable=False,
    )

    r_quantity = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # ------------------------------------------------------
    # Cost snapshot at time of sale
    # ------------------------------------------------------

    cost_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    # ------------------------------------------------------
    # Selling price
    # ------------------------------------------------------

    unit_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    discount = Column(
        Numeric(12, 2),
        default=0,
    )

    gst = Column(
        Numeric(12, 2),
        default=0,
    )

    total_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    sale = relationship(
        "Sale",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
        back_populates="sale_items",
    )