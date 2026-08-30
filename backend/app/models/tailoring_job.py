from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class TailoringJob(Base):
    __tablename__ = "tailoring_jobs"

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
        index=True,
    )

    job_number = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # ======================================================
    # CUSTOMER ORDER LINKS
    # ======================================================

    bill_id = Column(
        Integer,
        ForeignKey(
            "bills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    bill_item_id = Column(
        Integer,
        ForeignKey(
            "bill_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sale_item_id = Column(
        Integer,
        ForeignKey(
            "sale_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    customer_id = Column(
        Integer,
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ======================================================
    # TAILOR
    #
    # Tailor uses the existing Supplier master.
    # ======================================================

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    variant_id = Column(
        Integer,
        ForeignKey(
            "product_variants.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # ======================================================
    # K / R
    # ======================================================

    stock_type = Column(
        String(5),
        nullable=False,
    )

    # ======================================================
    # QUANTITIES
    # ======================================================

    quantity = Column(
        Integer,
        nullable=False,
    )

    received_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    delivered_quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ======================================================
    # STATUS
    #
    # Assigned
    # In Stitching
    # Partially Ready
    # Ready
    # Customer Notified
    # Delivered
    # Cancelled
    # ======================================================

    status = Column(
        String(30),
        nullable=False,
        default="Assigned",
        index=True,
    )

    # ======================================================
    # MONEY
    #
    # Supplier/tailor payable integration will connect to
    # this field in the next stage.
    # ======================================================

    stitching_charge = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    # ======================================================
    # DATES
    # ======================================================

    expected_date = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    stitching_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    received_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer_notified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    delivered_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    instructions = Column(
        Text,
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    bill = relationship(
        "Bill",
    )

    bill_item = relationship(
        "BillItem",
    )

    sale_item = relationship(
        "SaleItem",
    )

    customer = relationship(
        "Customer",
    )

    supplier = relationship(
        "Supplier",
    )

    variant = relationship(
        "ProductVariant",
    )

    tailor_payments = relationship(
        "TailorPayment",
        back_populates="tailoring_job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
