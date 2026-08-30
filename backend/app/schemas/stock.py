from pydantic import BaseModel, Field


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