from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class BillItem(Base):
    __tablename__ = "bill_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    bill_id = Column(
        Integer,
        ForeignKey(
            "bills.id",
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

    # -----------------------------
    # Ordered Quantity
    # -----------------------------
    ordered_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Delivered Quantity
    # -----------------------------
    delivered_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Pending Quantity
    # -----------------------------
    pending_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Delivered from K Stock
    # -----------------------------
    k_delivered_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Delivered from R Stock
    # -----------------------------
    r_delivered_qty = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Ordered from K Stock
    # -----------------------------
    k_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Ordered from R Stock
    # -----------------------------
    r_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # -----------------------------
    # Pricing
    # -----------------------------
    selling_price = Column(
        Numeric(12, 2),
        nullable=False,
    )

    discount = Column(
        Numeric(12, 2),
        default=0,
    )

    gst_percentage = Column(
        Numeric(5, 2),
        default=0,
    )

    gst = Column(
        Numeric(12, 2),
        default=0,
    )

    total = Column(
        Numeric(12, 2),
        nullable=False,
    )

    # -----------------------------
    # Delivery Status
    # -----------------------------
    item_status = Column(
        String(20),
        nullable=False,
        default="Delivered",
    )

    # -----------------------------
    # Relationships
    # -----------------------------
    bill = relationship(
        "Bill",
        back_populates="items",
    )

    variant = relationship(
        "ProductVariant",
        back_populates="bill_items",
    )