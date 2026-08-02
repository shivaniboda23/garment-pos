from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base



class Shop(Base):
    __tablename__ = "shops"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    shop_name = Column(
        String(200),
        nullable=False,
    )

    owner_name = Column(
        String(150),
    )

    phone = Column(
        String(20),
    )

    email = Column(
        String(150),
    )

    address = Column(
        String(500),
    )

    logo = Column(
        String(500),
    )

    users = relationship(
        "User",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    products = relationship(
        "Product",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    suppliers = relationship(
        "Supplier",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    purchases = relationship(
        "Purchase",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    purchase_returns = relationship(
        "PurchaseReturn",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    customers = relationship(
        "Customer",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    sales = relationship(
        "Sale",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    bills = relationship(
        "Bill",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    expense_categories = relationship(
        "ExpenseCategory",
        back_populates="shop",
        cascade="all, delete-orphan",
    )

    expenses = relationship(
        "Expense",
        back_populates="shop",
        cascade="all, delete-orphan",
    )
