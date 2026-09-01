from typing import Literal, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


# ==========================================================
# CREATE STOCK
# ==========================================================

class StockCreate(BaseModel):

    variant_id: int

    k_stock: int = Field(
        default=0,
        ge=0,
    )

    r_stock: int = Field(
        default=0,
        ge=0,
    )

    # Total minimum
    minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # K minimum
    k_minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # R minimum
    r_minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # Total maximum
    maximum_stock: int = Field(
        default=0,
        ge=0,
    )


# ==========================================================
# UPDATE STOCK
# ==========================================================

class StockUpdate(BaseModel):

    k_stock: int = Field(
        ge=0,
    )

    r_stock: int = Field(
        ge=0,
    )

    # Total minimum
    minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # K minimum
    k_minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # R minimum
    r_minimum_stock: int = Field(
        default=0,
        ge=0,
    )

    # Total maximum
    maximum_stock: int = Field(
        default=0,
        ge=0,
    )


# ==========================================================
# PHYSICAL STOCK ADJUSTMENT
# ==========================================================

class PhysicalStockAdjustmentCreate(BaseModel):

    variant_id: int

    stock_type: Literal["K", "R"]

    counted_quantity: int = Field(
        ge=0,
    )

    reason: str = Field(
        min_length=1,
        max_length=100,
    )

    notes: Optional[str] = None

    @field_validator("reason")
    @classmethod
    def validate_reason(
        cls,
        value: str,
    ) -> str:
        reason = value.strip()

        if not reason:
            raise ValueError(
                "Reason is required."
            )

        return reason


class PhysicalStockAdjustmentResponse(BaseModel):

    success: bool

    variant_id: int

    stock_type: Literal["K", "R"]

    quantity_before: int

    quantity_after: int

    quantity_change: int

    reason: str

    movement_id: int

    reference_number: Optional[str] = None


# ==========================================================
# RESPONSE
# ==========================================================

class StockResponse(BaseModel):

    id: int

    variant_id: int

    k_stock: int

    r_stock: int

    quantity: int

    minimum_stock: int

    k_minimum_stock: int

    r_minimum_stock: int

    maximum_stock: int

    class Config:
        from_attributes = True
