from sqlalchemy import (
    Column,
    Integer,
    Numeric,
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

    # -----------------------------------
    # Total Quantity Sold
    # -----------------------------------
    quantity = Column(
        Integer,
        nullable=False,
    )

    # -----------------------------------
    # Manufacturing (K) Quantity Sold
    # -----------------------------------
    k_quantity = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # -----------------------------------
    # Ready Purchase (R) Quantity Sold
    # -----------------------------------
    r_quantity = Column(
        Integer,
        default=0,
        nullable=False,
    )

    unit_price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    discount = Column(
        Numeric(10, 2),
        default=0,
    )

    gst = Column(
        Numeric(10, 2),
        default=0,
    )

    total_price = Column(
        Numeric(10, 2),
        nullable=False,
    )

    # -----------------------------------
    # Relationships
    # -----------------------------------
    sale = relationship(
        "Sale",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
        back_populates="sale_items",
    )