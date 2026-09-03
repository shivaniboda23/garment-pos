from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.purchase_return import (
    PurchaseReturnCreate,
)

from app.crud.purchase_return import (
    create_purchase_return,
    get_all_purchase_returns,
    get_purchase_return_by_id,
    search_purchase_return,
    supplier_returns,
)


router = APIRouter(
    prefix="/purchase-return",
    tags=["Purchase Return"],
)


# ==========================================================
# CREATE PURCHASE RETURN
# ==========================================================

@router.post("/create")
def create_purchase_return_api(
    data: PurchaseReturnCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        purchase_return = create_purchase_return(
            db=db,
            shop_id=current_user.shop_id,
            data=data,
        )

        return {
            "success": True,
            "message": "Purchase Return Created Successfully",
            "return_id": purchase_return.id,
            "return_number": purchase_return.return_number,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# ==========================================================
# GET ALL PURCHASE RETURNS
# ==========================================================

@router.get("/")
def purchase_return_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    returns = get_all_purchase_returns(
        db=db,
        shop_id=current_user.shop_id,
    )

    return returns


# ==========================================================
# GET PURCHASE RETURN DETAILS
# ==========================================================

@router.get("/{return_id}")
def purchase_return_details(
    return_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    purchase_return = get_purchase_return_by_id(
        db=db,
        shop_id=current_user.shop_id,
        return_id=return_id,
    )

    if purchase_return is None:

        raise HTTPException(
            status_code=404,
            detail="Purchase Return Not Found",
        )

    return purchase_return


# ==========================================================
# SEARCH RETURN NUMBER
# ==========================================================

@router.get("/search/{return_number}")
def search_return(
    return_number: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return search_purchase_return(
        db=db,
        shop_id=current_user.shop_id,
        return_number=return_number,
    )


# ==========================================================
# SUPPLIER RETURNS
# ==========================================================

@router.get("/supplier/{supplier_id}")
def supplier_return_history(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return supplier_returns(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )
