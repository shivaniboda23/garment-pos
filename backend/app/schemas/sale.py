from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, field_validator


# ==========================================================
# SALE ITEM CREATE
# ==========================================================

class SaleItemCreate(BaseModel):

    variant_id: int

    quantity: int

    k_quantity: int = 0

    r_quantity: int = 0

    discount: Decimal = Decimal("0")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(
        cls,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Quantity must be greater than 0"
            )

        return value

    @field_validator("k_quantity")
    @classmethod
    def validate_k_quantity(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "K Quantity cannot be negative"
            )

        return value

    @field_validator("r_quantity")
    @classmethod
    def validate_r_quantity(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "R Quantity cannot be negative"
            )

        return value

    @field_validator("discount")
    @classmethod
    def validate_discount(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Discount cannot be negative"
            )

        return value


# ==========================================================
# SALE CREATE
# ==========================================================

class SaleCreate(BaseModel):

    shop_id: int

    customer_id: Optional[int] = None

    payment_method: str = "Cash"

    discount: Decimal = Decimal("0")

    items: List[SaleItemCreate]

    @field_validator("discount")
    @classmethod
    def validate_discount(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Discount cannot be negative"
            )

        return value


# ==========================================================
# SALE ITEM RESPONSE
# ==========================================================

class SaleItemResponse(BaseModel):

    id: int

    variant_id: int

    quantity: int

    stock_type: str

    k_quantity: int

    r_quantity: int

    cost_price: Decimal

    unit_price: Decimal

    discount: Decimal

    gst: Decimal

    total_price: Decimal

    class Config:
        from_attributes = True


# ==========================================================
# SALE RESPONSE
# ==========================================================

class SaleResponse(BaseModel):

    id: int

    invoice_number: str

    customer_id: Optional[int]

    subtotal: Decimal

    discount: Decimal

    gst_amount: Decimal

    total_amount: Decimal

    payment_method: str

    status: str

    items: List[SaleItemResponse]

    class Config:
        from_attributes = True