from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_id = Column(
        Integer,
        ForeignKey(
            "purchases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    variant_id = Column(
        Integer,
        ForeignKey(
            "product_variants.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
    )

    stock_type = Column(
        String(1),
        nullable=False,
    )

    cost_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    gst_percentage = Column(
        Numeric(5, 2),
        default=0,
    )

    discount = Column(
        Numeric(12, 2),
        default=0,
    )

    total = Column(
        Numeric(12, 2),
        nullable=False,
    )

    purchase = relationship(
        "Purchase",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
        back_populates="purchase_items",
    )

    