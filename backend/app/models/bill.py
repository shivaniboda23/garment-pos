from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Text,
    ForeignKey,
    DateTime,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sale_id = Column(
        Integer,
        ForeignKey(
            "sales.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        unique=True,
    )

    invoice_number = Column(
        String(30),
        unique=True,
        nullable=False,
    )

    shop_id = Column(
        Integer,
        ForeignKey(
            "shops.id",
        ),
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
        ),
        nullable=True,
    )

    subtotal = Column(
        Numeric(12, 2),
        default=0,
    )

    discount = Column(
        Numeric(12, 2),
        default=0,
    )

    gst = Column(
        Numeric(12, 2),
        default=0,
    )

    grand_total = Column(
        Numeric(12, 2),
        default=0,
    )

    payment_method = Column(
        String(30),
        default="Cash",
    )

    payment_status = Column(
        String(20),
        default="Pending",
    )

    remarks = Column(
        Text,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    bill_status = Column(
        String(20),
        default="Completed",
    )

    shop = relationship(
        "Shop",
        back_populates="bills",
    )

    customer = relationship(
        "Customer",
        back_populates="bills",
    )

    sale = relationship(
        "Sale",
        back_populates="bill",
        uselist=False,
    )

    items = relationship(
        "BillItem",
        back_populates="bill",
        cascade="all, delete-orphan",
    )

    payments = relationship(
        "Payment",
        back_populates="bill",
        cascade="all, delete-orphan",
    )