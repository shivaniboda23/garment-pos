from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.crud.tailor_payment import (
    create_tailor_payment,
    get_all_tailor_payments,
    get_job_payments,
    get_tailor_payments,
    get_job_payment_summary,
    get_tailor_balance_summary,
    get_all_tailor_dues,
    get_tailor_ledger,
)
from app.schemas.tailor_payment import (
    TailorPaymentCreate,
    TailorPaymentResponse,
    TailoringJobPaymentSummary,
    TailorBalanceSummary,
    TailorDueItem,
    TailorLedgerResponse,
)


router = APIRouter(
    prefix="/tailor-payments",
    tags=["Tailor Payments"],
)


@router.post(
    "/create",
    response_model=TailorPaymentResponse,
)
def add_tailor_payment(
    request: TailorPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_tailor_payment(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )


@router.get(
    "/",
    response_model=list[TailorPaymentResponse],
)
def payment_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_tailor_payments(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/dues",
    response_model=list[TailorDueItem],
)
def tailor_dues(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_tailor_dues(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/job/{job_id}",
    response_model=list[TailorPaymentResponse],
)
def job_payment_history(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_job_payments(
        db=db,
        shop_id=current_user.shop_id,
        job_id=job_id,
    )


@router.get(
    "/job/{job_id}/summary",
    response_model=TailoringJobPaymentSummary,
)
def job_payment_summary(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_job_payment_summary(
        db=db,
        shop_id=current_user.shop_id,
        job_id=job_id,
    )


@router.get(
    "/tailor/{supplier_id}",
    response_model=list[TailorPaymentResponse],
)
def tailor_payment_history(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_tailor_payments(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )


@router.get(
    "/tailor/{supplier_id}/summary",
    response_model=TailorBalanceSummary,
)
def tailor_balance_summary(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_tailor_balance_summary(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )


@router.get(
    "/tailor/{supplier_id}/ledger",
    response_model=TailorLedgerResponse,
)
def tailor_ledger(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_tailor_ledger(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )
