from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    purchase_return_id = Column(
        Integer,
        ForeignKey(
            "purchase_returns.id",
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

    cost_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    total = Column(
        Numeric(12, 2),
        nullable=False,
    )

    purchase_return = relationship(
        "PurchaseReturn",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
    )