from decimal import Decimal
from typing import List

from pydantic import BaseModel, field_validator


# ==========================================================
# Purchase Return Item Create
# ==========================================================

class PurchaseReturnItemCreate(BaseModel):

    variant_id: int

    quantity: int

    k_quantity: int = 0

    r_quantity: int = 0

    cost_price: Decimal

    total: Decimal

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError("Quantity must be greater than 0")
        return value

    @field_validator("k_quantity")
    @classmethod
    def validate_k_quantity(cls, value):
        if value < 0:
            raise ValueError("K Quantity cannot be negative")
        return value

    @field_validator("r_quantity")
    @classmethod
    def validate_r_quantity(cls, value):
        if value < 0:
            raise ValueError("R Quantity cannot be negative")
        return value


# ==========================================================
# Purchase Return Create
# ==========================================================

class PurchaseReturnCreate(BaseModel):

    purchase_id: int

    supplier_id: int

    reason: str | None = None

    total_amount: Decimal

    items: List[PurchaseReturnItemCreate]


# ==========================================================
# Purchase Return Item Response
# ==========================================================

class PurchaseReturnItemResponse(BaseModel):

    variant_id: int

    quantity: int

    k_quantity: int

    r_quantity: int

    cost_price: Decimal

    total: Decimal

    class Config:
        from_attributes = True


# ==========================================================
# Purchase Return Response
# ==========================================================

class PurchaseReturnResponse(BaseModel):

    id: int

    return_number: str

    purchase_id: int

    supplier_id: int

    reason: str | None

    total_amount: Decimal

    status: str

    items: List[PurchaseReturnItemResponse] = []

    class Config:
        from_attributes = True