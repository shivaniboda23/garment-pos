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


class TailorPayment(Base):
    __tablename__ = "tailor_payments"

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

    supplier_id = Column(
        Integer,
        ForeignKey(
            "suppliers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    tailoring_job_id = Column(
        Integer,
        ForeignKey(
            "tailoring_jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    tailoring_job = relationship(
        "TailoringJob",
        back_populates="tailor_payments",
    )

    supplier = relationship(
        "Supplier",
    )

    shop = relationship(
        "Shop",
    )
