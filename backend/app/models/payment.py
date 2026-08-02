from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    bill_id = Column(
        Integer,
        ForeignKey("bills.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_method = Column(
        String(30),
        nullable=False,
    )

    transaction_reference = Column(
        String(100),
        nullable=True,
    )

    bill = relationship(
        "Bill",
        back_populates="payments",
    )