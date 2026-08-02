from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class SaleReturnItem(Base):
    __tablename__ = "sale_return_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sale_return_id = Column(
        Integer,
        ForeignKey(
            "sale_returns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    variant_id = Column(
        Integer,
        ForeignKey(
            "product_variants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
    )

    unit_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    refund_amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    sale_return = relationship(
        "SaleReturn",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
    )