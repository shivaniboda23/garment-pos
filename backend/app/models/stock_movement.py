from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    func,
)

from app.db.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

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
    # MOVEMENT
    # ======================================================

    movement_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    stock_type = Column(
        String(5),
        nullable=False,
        index=True,
    )

    quantity = Column(
        Integer,
        nullable=False,
    )

    quantity_before = Column(
        Integer,
        nullable=False,
        default=0,
    )

    quantity_after = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ======================================================
    # REFERENCE
    # ======================================================

    reference_type = Column(
        String(30),
        nullable=True,
    )

    reference_id = Column(
        Integer,
        nullable=True,
    )

    reference_number = Column(
        String(100),
        nullable=True,
    )

    # ======================================================
    # REASON / NOTES
    # ======================================================

    reason = Column(
        String(100),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    # ======================================================
    # CREATED
    # ======================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )