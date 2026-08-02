from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# Expense Category
# ==========================================================

class ExpenseCategoryCreate(BaseModel):
    shop_id: int
    category_name: str
    description: Optional[str] = None


class ExpenseCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExpenseCategoryResponse(BaseModel):
    id: int
    shop_id: int
    category_name: str
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ==========================================================
# Expense
# ==========================================================

class ExpenseCreate(BaseModel):
    shop_id: int
    category_id: int
    amount: Decimal
    payment_method: str = "Cash"
    reference_number: Optional[str] = None
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    shop_id: int
    category_id: int
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    description: Optional[str]
    expense_date: datetime

    class Config:
        from_attributes = True