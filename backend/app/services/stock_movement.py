from sqlalchemy.orm import Session

from app.models.stock_movement import StockMovement


# ==========================================================
# RECORD STOCK MOVEMENT
# ==========================================================

def record_stock_movement(
    db: Session,
    shop_id: int,
    variant_id: int,
    movement_type: str,
    stock_type: str,
    quantity: int,
    quantity_before: int,
    quantity_after: int,
    reference_type: str | None = None,
    reference_id: int | None = None,
    reference_number: str | None = None,
    reason: str | None = None,
    notes: str | None = None,
):
    movement = StockMovement(
        shop_id=shop_id,
        variant_id=variant_id,
        movement_type=movement_type,
        stock_type=stock_type,
        quantity=quantity,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=reference_type,
        reference_id=reference_id,
        reference_number=reference_number,
        reason=reason,
        notes=notes,
    )

    db.add(movement)

    return movement