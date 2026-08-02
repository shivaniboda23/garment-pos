from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel


# ==========================
# Purchase Item Create
# ==========================

class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int
    stock_type: str
    cost_price: Decimal
    gst_percentage: Decimal = 0
    discount: Decimal = 0
    total: Decimal


# ==========================
# Purchase Create
# ==========================

class PurchaseCreate(BaseModel):
    supplier_id: int
    supplier_invoice: Optional[str] = None

    subtotal: Decimal
    discount: Decimal = 0
    gst: Decimal = 0
    grand_total: Decimal

    paid_amount: Decimal = 0
    balance_amount: Decimal = 0

    items: List[PurchaseItemCreate]


# ==========================
# Purchase Item Response
# ==========================

class PurchaseItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    stock_type: str
    cost_price: Decimal
    gst_percentage: Decimal
    discount: Decimal
    total: Decimal

    class Config:
        from_attributes = True


# ==========================
# Purchase List Response
# ==========================

class PurchaseResponse(BaseModel):
    id: int
    invoice_number: str
    supplier_invoice: Optional[str]

    supplier_id: int
    shop_id: int

    subtotal: Decimal
    discount: Decimal
    gst: Decimal
    grand_total: Decimal

    paid_amount: Decimal
    balance_amount: Decimal

    status: str

    created_at: datetime

    class Config:
        from_attributes = True


# ==========================
# Purchase Detail Response
# ==========================

class PurchaseDetailResponse(PurchaseResponse):

    items: List[PurchaseItemResponse]

    class Config:
        from_attributes = True