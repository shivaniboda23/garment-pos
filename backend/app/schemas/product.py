from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    category_id: Optional[int] = None
    brand_id: Optional[int] = None

    product_name: str
    description: Optional[str] = None

    hsn_code: Optional[str] = None

    gst_percentage: Decimal = 0

    cost_price: Decimal = 0

    selling_price: Decimal = 0


class ProductResponse(BaseModel):
    id: int

    product_code: str

    product_name: str

    selling_price: Decimal

    gst_percentage: Decimal

    class Config:
        from_attributes = True