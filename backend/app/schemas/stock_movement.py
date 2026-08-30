from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# CREATE STOCK ADJUSTMENT
# ==========================================================

class StockAdjustmentCreate(BaseModel):

    variant_id: int

    stock_type: str

    quantity: int

    reason: str

    notes: Optional[str] = None


# ==========================================================
# STOCK MOVEMENT RESPONSE
# ==========================================================

class StockMovementResponse(BaseModel):

    id: int

    shop_id: int

    variant_id: int

    movement_type: str

    stock_type: str

    quantity: int

    quantity_before: int

    quantity_after: int

    reference_type: Optional[str]

    reference_id: Optional[int]

    reference_number: Optional[str]

    reason: Optional[str]

    notes: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True