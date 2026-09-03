from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.purchase import PurchaseCreate

from app.crud.purchase import (
    create_purchase,
    get_all_purchases,
    get_purchase_by_id,
    search_purchase_invoice,
    search_purchase_supplier,
    get_pending_purchases,
    get_completed_purchases,
)

router = APIRouter(
    prefix="/purchase",
    tags=["Purchase"],
)


# ==========================================================
# CREATE PURCHASE
# ==========================================================

@router.post("/create")
def create_purchase_api(
    data: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchase = create_purchase(
        db=db,
        shop_id=current_user.shop_id,
        data=data,
    )

    return {
        "success": True,
        "message": "Purchase Created Successfully",
        "purchase_id": purchase.id,
    }


# ==========================================================
# PURCHASE HISTORY
# ==========================================================

@router.get("/")
def purchase_history(
    invoice: Optional[str] = None,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchases = get_all_purchases(
        db=db,
        shop_id=current_user.shop_id,
        invoice=invoice,
        supplier_id=supplier_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )

    return purchases


# ==========================================================
# PURCHASE DETAILS
# ==========================================================

@router.get("/{purchase_id}")
def purchase_details(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchase = get_purchase_by_id(
        db=db,
        purchase_id=purchase_id,
        shop_id=current_user.shop_id,
    )

    if purchase is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found",
        )

    return purchase


# ==========================================================
# SEARCH PURCHASE BY INVOICE
# ==========================================================

@router.get("/search/invoice/{invoice}")
def search_invoice(
    invoice: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchases = search_purchase_invoice(
        db=db,
        shop_id=current_user.shop_id,
        invoice=invoice,
    )

    return purchases


# ==========================================================
# SEARCH PURCHASE BY SUPPLIER
# ==========================================================

@router.get("/supplier/{supplier_id}")
def supplier_purchase_history(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchases = search_purchase_supplier(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )

    return purchases


# ==========================================================
# PENDING PURCHASES
# ==========================================================

@router.get("/status/pending")
def pending_purchases(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_pending_purchases(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# COMPLETED PURCHASES
# ==========================================================

@router.get("/status/completed")
def completed_purchases(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_completed_purchases(
        db=db,
        shop_id=current_user.shop_id,
    )
