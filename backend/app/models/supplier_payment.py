from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    Text,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

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

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    purchase_id = Column(
        Integer,
        ForeignKey(
            "purchases.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_method = Column(
        String(30),
        nullable=False,
    )

    reference_number = Column(
        String(100),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    payment_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    shop = relationship(
        "Shop",
        back_populates="supplier_payments",
    )

    supplier = relationship(
        "Supplier",
        back_populates="payments",
    )

    purchase = relationship(
        "Purchase",
        back_populates="payments",
    )