from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.crud.customer_payment import (
    create_customer_payment,
    get_bill_payments,
    get_customer_due_summary,
    get_all_customer_dues,
)

from app.schemas.customer_payment import (
    CustomerPaymentCreate,
    CustomerPaymentResponse,
)


router = APIRouter(
    prefix="/customer-payment",
    tags=["Customer Payment"],
)


# ==========================================================
# CREATE CUSTOMER PAYMENT
# ==========================================================

@router.post(
    "/create",
    response_model=CustomerPaymentResponse,
)
def create_customer_payment_api(
    data: CustomerPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return create_customer_payment(
        db=db,
        shop_id=current_user.shop_id,
        data=data,
    )


# ==========================================================
# PAYMENTS FOR BILL
# ==========================================================

@router.get(
    "/bill/{bill_id}",
    response_model=list[
        CustomerPaymentResponse
    ],
)
def bill_payment_history(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return get_bill_payments(
        db=db,
        shop_id=current_user.shop_id,
        bill_id=bill_id,
    )


# ==========================================================
# CUSTOMER DUE SUMMARY
# ==========================================================

@router.get(
    "/customer/{customer_id}/summary",
)
def customer_due_summary(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return get_customer_due_summary(
        db=db,
        shop_id=current_user.shop_id,
        customer_id=customer_id,
    )


# ==========================================================
# ALL CUSTOMER DUES
# ==========================================================

@router.get(
    "/",
)
def customer_due_list(
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    return get_all_customer_dues(
        db=db,
        shop_id=current_user.shop_id,
    )