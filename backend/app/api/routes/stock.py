from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.crud.stock import (
    create_stock,
    get_all_stock,
    update_stock,
)

from app.schemas.stock import (
    StockCreate,
    StockUpdate,
    StockResponse,
)

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
)


# ==========================================
# Create Stock
# ==========================================

@router.post(
    "",
    response_model=StockResponse,
)
def add_stock(
    request: StockCreate,
    db: Session = Depends(get_db),
):

    stock = create_stock(
        db,
        request,
    )

    if not stock:

        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return stock


# ==========================================
# List Stock
# ==========================================

@router.get(
    "",
    response_model=list[StockResponse],
)
def list_stock(
    db: Session = Depends(get_db),
):

    return get_all_stock(db)


# ==========================================
# Update Stock
# ==========================================

@router.put(
    "/{variant_id}",
    response_model=StockResponse,
)
def edit_stock(
    variant_id: int,
    request: StockUpdate,
    db: Session = Depends(get_db),
):

    stock = update_stock(
        db=db,
        variant_id=variant_id,
        data=request,
    )

    if not stock:

        raise HTTPException(
            status_code=404,
            detail="Stock not found",
        )

    return stock