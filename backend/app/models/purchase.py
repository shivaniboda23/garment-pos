from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    )

    invoice_number = Column(
        String(100),
        nullable=False,
    )

    supplier_invoice = Column(
        String(100),
    )

    subtotal = Column(
        Numeric(12,2),
        default=0,
    )

    discount = Column(
        Numeric(12,2),
        default=0,
    )

    gst = Column(
        Numeric(12,2),
        default=0,
    )

    grand_total = Column(
        Numeric(12,2),
        default=0,
    )

    paid_amount = Column(
        Numeric(12,2),
        default=0,
    )

    balance_amount = Column(
        Numeric(12,2),
        default=0,
    )

    status = Column(
        String(30),
        default="Pending",
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
        back_populates="purchases",
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchases",
    )

    items = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
    )