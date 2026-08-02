from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductVariantCreate(BaseModel):
    product_id: int

    sku: str
    barcode: str
    size: str

    color: Optional[str] = None

    reorder_level: int = 5

    cost_price: Decimal = 0

    selling_price: Decimal = 0


class ProductVariantUpdate(BaseModel):
    product_id: int

    size: str

    color: Optional[str] = None

    reorder_level: int = 5

    cost_price: Decimal = 0

    selling_price: Decimal = 0


class ProductVariantResponse(BaseModel):
    id: int

    product_id: int

    sku: str

    barcode: str

    size: str

    color: Optional[str]

    quantity: int

    reorder_level: int

    cost_price: Decimal

    selling_price: Decimal

    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )