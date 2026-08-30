from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

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

    category_name = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        String(300),
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    shop = relationship(
        "Shop",
        back_populates="expense_categories",
    )

    expenses = relationship(
        "Expense",
        back_populates="category",
    )