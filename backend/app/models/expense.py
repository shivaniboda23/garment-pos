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


class Expense(Base):
    __tablename__ = "expenses"

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

    category_id = Column(
        Integer,
        ForeignKey(
            "expense_categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_method = Column(
        String(30),
        default="Cash",
    )

    reference_number = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        String(500),
        nullable=True,
    )

    expense_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
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
        back_populates="expenses",
    )

    category = relationship(
        "ExpenseCategory",
        back_populates="expenses",
    )