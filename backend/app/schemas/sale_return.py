from decimal import Decimal
from typing import List

from pydantic import BaseModel


# ==========================================================
# CREATE RETURN ITEM
# ==========================================================

class SaleReturnItemCreate(BaseModel):
    variant_id: int
    quantity: int


# ==========================================================
# CREATE SALE RETURN
# ==========================================================

class SaleReturnCreate(BaseModel):
    sale_id: int
    customer_id: int
    reason: str | None = None
    refund_amount: Decimal

    items: List[SaleReturnItemCreate]


# ==========================================================
# RESPONSE RETURN ITEM
# ==========================================================

class SaleReturnItemResponse(BaseModel):
    id: int
    variant_id: int
    quantity: int
    unit_price: Decimal
    refund_amount: Decimal

    class Config:
        from_attributes = True


# ==========================================================
# RESPONSE SALE RETURN
# ==========================================================

class SaleReturnResponse(BaseModel):
    id: int
    sale_id: int
    customer_id: int
    return_number: str
    reason: str | None = None
    refund_amount: Decimal
    status: str

    items: List[SaleReturnItemResponse]

    class Config:
        from_attributes = True