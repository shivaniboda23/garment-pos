from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, field_validator


# ==========================================================
# PURCHASE RETURN ITEM CREATE
# ==========================================================

class PurchaseReturnItemCreate(BaseModel):

    variant_id: int

    quantity: int

    k_quantity: int = 0

    r_quantity: int = 0

    cost_price: Decimal

    total: Decimal

    # ------------------------------------------------------
    # Quantity Validation
    # ------------------------------------------------------

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value):

        if value <= 0:
            raise ValueError(
                "Quantity must be greater than 0."
            )

        return value

    # ------------------------------------------------------
    # K Quantity Validation
    # ------------------------------------------------------

    @field_validator("k_quantity")
    @classmethod
    def validate_k_quantity(cls, value):

        if value < 0:
            raise ValueError(
                "K Quantity cannot be negative."
            )

        return value

    # ------------------------------------------------------
    # R Quantity Validation
    # ------------------------------------------------------

    @field_validator("r_quantity")
    @classmethod
    def validate_r_quantity(cls, value):

        if value < 0:
            raise ValueError(
                "R Quantity cannot be negative."
            )

        return value


# ==========================================================
# PURCHASE RETURN CREATE
# ==========================================================

class PurchaseReturnCreate(BaseModel):

    purchase_id: int

    supplier_id: int

    reason: str | None = None

    total_amount: Decimal

    items: List[PurchaseReturnItemCreate]

    # ------------------------------------------------------
    # Items Validation
    # ------------------------------------------------------

    @field_validator("items")
    @classmethod
    def validate_items(cls, value):

        if not value:
            raise ValueError(
                "At least one purchase return item is required."
            )

        return value


# ==========================================================
# PURCHASE RETURN ITEM RESPONSE
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
# PURCHASE RETURN RESPONSE
# ==========================================================

class PurchaseReturnResponse(BaseModel):

    id: int

    return_number: str

    purchase_id: int

    supplier_id: int

    reason: str | None

    total_amount: Decimal

    status: str

    items: List[PurchaseReturnItemResponse] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True