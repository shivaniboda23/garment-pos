from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class SaleReturn(Base):
    __tablename__ = "sale_returns"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    shop_id = Column(
        Integer,
        ForeignKey(
            "shops.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    sale_id = Column(
        Integer,
        ForeignKey(
            "sales.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    return_number = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    reason = Column(
        String(255),
    )

    refund_amount = Column(
        Numeric(12, 2),
        default=0,
    )

    status = Column(
        String(30),
        default="Completed",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    shop = relationship(
        "Shop",
    )

    sale = relationship(
        "Sale",
    )

    customer = relationship(
        "Customer",
    )

    items = relationship(
        "SaleReturnItem",
        back_populates="sale_return",
        cascade="all, delete-orphan",
    )