from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )

    supplier_code = Column(
        String(30),
        unique=True,
        nullable=True,
    )

    supplier_name = Column(
        String(150),
        nullable=False,
    )

    contact_person = Column(
        String(100),
    )

    mobile = Column(
        String(20),
    )

    email = Column(
        String(150),
    )

    gst_number = Column(
        String(30),
    )

    pan_number = Column(
        String(20),
    )

    address = Column(Text)

    city = Column(
        String(80),
    )

    state = Column(
        String(80),
    )

    pincode = Column(
        String(20),
    )

    opening_balance = Column(
        Numeric(12, 2),
        default=0,
    )

    payment_terms = Column(
        Integer,
        default=30,
    )

    credit_limit = Column(
        Numeric(12, 2),
        default=0,
    )

    upi_id = Column(
        String(100),
    )

    bank_name = Column(
        String(100),
    )

    account_number = Column(
        String(50),
    )

    ifsc_code = Column(
        String(20),
    )

    notes = Column(Text)

    is_active = Column(
        Boolean,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    shop = relationship(
        "Shop",
        back_populates="suppliers",
    )

   
    purchases = relationship(
         "Purchase",
         back_populates="supplier",
         cascade="all, delete-orphan",
     )