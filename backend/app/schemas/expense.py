from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# EXPENSE CATEGORY
# ==========================================================

class ExpenseCategoryCreate(BaseModel):

    category_name: str

    description: Optional[str] = None


class ExpenseCategoryUpdate(BaseModel):

    category_name: Optional[str] = None

    description: Optional[str] = None

    is_active: Optional[bool] = None


class ExpenseCategoryResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    shop_id: int

    category_name: str

    description: Optional[str]

    is_active: bool


# ==========================================================
# EXPENSE CREATE
# ==========================================================

class ExpenseCreate(BaseModel):

    category_id: int

    amount: Decimal = Field(
        gt=0,
    )

    payment_method: str = "Cash"

    reference_number: Optional[str] = None

    description: Optional[str] = None

    expense_date: Optional[datetime] = None


# ==========================================================
# EXPENSE UPDATE
# ==========================================================

class ExpenseUpdate(BaseModel):

    category_id: Optional[int] = None

    amount: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    payment_method: Optional[str] = None

    reference_number: Optional[str] = None

    description: Optional[str] = None

    expense_date: Optional[datetime] = None


# ==========================================================
# EXPENSE RESPONSE
# ==========================================================

class ExpenseResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    shop_id: int

    category_id: int

    amount: Decimal

    payment_method: str

    reference_number: Optional[str]

    description: Optional[str]

    expense_date: datetime