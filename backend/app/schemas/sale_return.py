from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator


# ==========================================================
# CREATE RETURN ITEM
# ==========================================================

class SaleReturnItemCreate(BaseModel):

    variant_id: int

    quantity: int

    k_quantity: int = 0

    r_quantity: int = 0

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):
        if value <= 0:
            raise ValueError(
                "Return quantity must be greater than zero."
            )
        return value

    @field_validator("k_quantity", "r_quantity")
    @classmethod
    def validate_stock_quantities(cls, value):
        if value < 0:
            raise ValueError(
                "Return stock quantity cannot be negative."
            )
        return value

    @model_validator(mode="after")
    def validate_split_quantities(self):
        if self.quantity != (
            self.k_quantity + self.r_quantity
        ):
            raise ValueError(
                "Return quantity must equal "
                "K quantity + R quantity."
            )
        return self


# ==========================================================
# CREATE SALE RETURN
# ==========================================================

class SaleReturnCreate(BaseModel):

    sale_id: int

    customer_id: Optional[int] = None

    reason: Optional[str] = None

    refund_amount: Decimal

    items: List[SaleReturnItemCreate]

    @field_validator("refund_amount")
    @classmethod
    def validate_refund_amount(cls, value):
        if value < 0:
            raise ValueError(
                "Refund amount cannot be negative."
            )
        return value

    @field_validator("items")
    @classmethod
    def validate_items(cls, value):
        if not value:
            raise ValueError(
                "At least one sale return item is required."
            )
        return value


# ==========================================================
# RESPONSE RETURN ITEM
# ==========================================================

class SaleReturnItemResponse(BaseModel):

    id: int

    variant_id: int

    quantity: int

    k_quantity: int

    r_quantity: int

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

    customer_id: Optional[int]

    return_number: str

    reason: Optional[str] = None

    refund_amount: Decimal

    status: str

    items: List[SaleReturnItemResponse]

    class Config:
        from_attributes = True