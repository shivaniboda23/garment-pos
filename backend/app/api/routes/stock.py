from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.crud.stock import (
    adjust_physical_stock,
    create_stock,
    get_all_stock,
    update_stock,
)

from app.schemas.stock import (
    StockCreate,
    PhysicalStockAdjustmentCreate,
    PhysicalStockAdjustmentResponse,
    StockUpdate,
    StockResponse,
)


router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
)


# ==========================================================
# PHYSICAL STOCK ADJUSTMENT
# ==========================================================

@router.post(
    "/adjust",
    response_model=(
        PhysicalStockAdjustmentResponse
    ),
)
def reconcile_physical_stock(
    request: PhysicalStockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return adjust_physical_stock(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )


# ==========================================================
# CREATE STOCK
# ==========================================================

@router.post(
    "",
    response_model=StockResponse,
)
def add_stock(
    request: StockCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stock = create_stock(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )

    if not stock:
        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return stock


# ==========================================================
# LIST STOCK
# ==========================================================

@router.get(
    "",
    response_model=list[StockResponse],
)
def list_stock(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_stock(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# UPDATE STOCK
# ==========================================================

@router.put(
    "/{variant_id}",
    response_model=StockResponse,
)
def edit_stock(
    variant_id: int,
    request: StockUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stock = update_stock(
        db=db,
        shop_id=current_user.shop_id,
        variant_id=variant_id,
        k_stock=request.k_stock,
        r_stock=request.r_stock,
        k_minimum_stock=(
            request.k_minimum_stock
        ),
        r_minimum_stock=(
            request.r_minimum_stock
        ),
        minimum_stock=(
            request.minimum_stock
        ),
        maximum_stock=(
            request.maximum_stock
        ),
    )

    if not stock:
        raise HTTPException(
            status_code=404,
            detail="Stock not found",
        )

    return stock
