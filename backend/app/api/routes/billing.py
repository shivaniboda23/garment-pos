from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.billing import (
    create_bill,
    get_all_bills,
    get_bill_by_id,
    search_bill,
)
from app.db.database import get_db
from app.dependencies import get_current_user
from app.schemas.billing import BillCreate, BillResponse

router = APIRouter(
    prefix="/billing",
    tags=["Billing"],
)


# ==========================================================
# CREATE BILL
# ==========================================================

@router.post(
    "/create",
    response_model=BillResponse,
)
def create_bill_api(
    request: BillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        bill = create_bill(
            db=db,
            shop_id=current_user.shop_id,
            data=request,
        )

        if bill is None:
            raise HTTPException(
                status_code=404,
                detail="Shop or customer not found",
            )

        return bill

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ==========================================================
# BILL HISTORY
# ==========================================================

@router.get(
    "",
    response_model=list[BillResponse],
)
def bill_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_bills(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# SEARCH BILL
# ==========================================================

@router.get(
    "/search",
    response_model=list[BillResponse],
)
def search_bills(
    q: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return search_bill(
        db=db,
        shop_id=current_user.shop_id,
        keyword=q,
    )


# ==========================================================
# BILL DETAILS
# ==========================================================

@router.get(
    "/{bill_id}",
    response_model=BillResponse,
)
def bill_details(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    bill = get_bill_by_id(
        db=db,
        bill_id=bill_id,
        shop_id=current_user.shop_id,
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found",
        )

    return bill
