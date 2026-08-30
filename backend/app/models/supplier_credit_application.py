from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
    DateTime,
    func,
)

from app.db.database import Base


class SupplierCreditApplication(Base):
    __tablename__ = "supplier_credit_applications"

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

    reference_number = Column(
        String(100),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    applied_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )