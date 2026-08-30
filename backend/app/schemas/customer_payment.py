from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ==========================================================
# CREATE CUSTOMER PAYMENT
# ==========================================================

class CustomerPaymentCreate(BaseModel):

    bill_id: int

    amount: Decimal = Field(
        gt=0,
    )

    payment_method: str

    transaction_reference: Optional[str] = None


# ==========================================================
# CUSTOMER PAYMENT RESPONSE
# ==========================================================

class CustomerPaymentResponse(BaseModel):

    id: int

    bill_id: int

    amount: Decimal

    payment_method: str

    transaction_reference: Optional[str] = None

    class Config:
        from_attributes = True