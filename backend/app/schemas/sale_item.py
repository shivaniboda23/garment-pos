from decimal import Decimal

from pydantic import BaseModel


class SaleItemCreate(BaseModel):

    variant_id: int

    quantity: int

    stock_type: str

    discount: Decimal = Decimal("0")