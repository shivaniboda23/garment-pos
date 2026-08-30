from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.crud.stock_movement import (
    get_stock_movements,
    get_variant_stock_movements,
    create_stock_adjustment,
    backfill_stock_movements,
)

from app.schemas.stock_movement import (
    StockAdjustmentCreate,
    StockMovementResponse,
)


router = APIRouter(
    prefix="/stock-movements",
    tags=["Stock Movements"],
)


# ==========================================================
# GET ALL STOCK MOVEMENTS
# ==========================================================

@router.get(
    "",
    response_model=list[
        StockMovementResponse
    ],
)
def stock_movement_history(
    variant_id: int | None = None,
    movement_type: str | None = None,
    stock_type: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return get_stock_movements(
        db=db,
        shop_id=current_user.shop_id,
        variant_id=variant_id,
        movement_type=movement_type,
        stock_type=stock_type,
    )


# ==========================================================
# HISTORICAL STOCK MOVEMENT BACKFILL
#
# IMPORTANT:
# This is intended as a ONE-TIME operation.
#
# The CRUD function will reject the request if stock
# movement rows already exist for this shop.
# ==========================================================

@router.post(
    "/backfill",
)
def historical_stock_backfill(
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return backfill_stock_movements(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# GET STOCK MOVEMENTS FOR ONE VARIANT
# ==========================================================

@router.get(
    "/variant/{variant_id}",
    response_model=list[
        StockMovementResponse
    ],
)
def variant_stock_movement_history(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return get_variant_stock_movements(
        db=db,
        shop_id=current_user.shop_id,
        variant_id=variant_id,
    )


# ==========================================================
# MANUAL STOCK ADJUSTMENT
# ==========================================================

@router.post(
    "/adjust",
    response_model=StockMovementResponse,
)
def stock_adjustment(
    data: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return create_stock_adjustment(
        db=db,
        shop_id=current_user.shop_id,
        data=data,
    )