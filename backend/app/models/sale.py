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


class Sale(Base):
    __tablename__ = "sales"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    shop_id = Column(
        Integer,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=True,
    )

    invoice_number = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    subtotal = Column(
        Numeric(10, 2),
        default=0,
    )

    discount = Column(
        Numeric(10, 2),
        default=0,
    )

    gst_amount = Column(
        Numeric(10, 2),
        default=0,
    )

    total_amount = Column(
        Numeric(10, 2),
        default=0,
    )

    payment_method = Column(
        String(30),
        default="Cash",
    )

    status = Column(
        String(20),
        default="Completed",
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

    shop = relationship(
        "Shop",
        back_populates="sales",
    )

    customer = relationship(
        "Customer",
        back_populates="sales",
    )

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )