from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"

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

    purchase_id = Column(
        Integer,
        ForeignKey(
            "purchases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    return_number = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    reason = Column(
        String(300),
    )

    total_amount = Column(
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
        back_populates="purchase_returns",
    )

    supplier = relationship(
        "Supplier",
    )

    purchase = relationship(
        "Purchase",
    )

    items = relationship(
        "PurchaseReturnItem",
        back_populates="purchase_return",
        cascade="all, delete-orphan",
    )