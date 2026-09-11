from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
    ForeignKeyConstraint,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class SaleReturn(Base):
    __tablename__ = "sale_returns"

    # MATCH SIMPLE intentionally leaves a null customer_id to the
    # application's existing null-safe equality validation.
    __table_args__ = (
        ForeignKeyConstraint(
            ["sale_id", "customer_id"],
            ["sales.id", "sales.customer_id"],
            name="fk_sale_returns_sale_customer",
            match="SIMPLE",
            onupdate="NO ACTION",
            ondelete="CASCADE",
        ),
    )

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

    sale_id = Column(
        Integer,
        ForeignKey(
            "sales.id",
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
        nullable=True,
    )

    return_number = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    reason = Column(
        String(255),
    )

    refund_amount = Column(
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
    )

    sale = relationship(
        "Sale",
        foreign_keys=[sale_id],
    )

    customer = relationship(
        "Customer",
    )

    items = relationship(
        "SaleReturnItem",
        back_populates="sale_return",
        cascade="all, delete-orphan",
    )
