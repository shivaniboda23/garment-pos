from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

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

    customer_name = Column(
        String(200),
        nullable=False,
    )

    phone = Column(
        String(15),
        unique=True,
        nullable=False,
    )

    email = Column(
        String(150),
        nullable=True,
    )

    address = Column(
        String(500),
        nullable=True,
    )

    gst_number = Column(
        String(30),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
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
        back_populates="customers",
    )

    sales = relationship(
        "Sale",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    bills = relationship(
        "Bill",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
