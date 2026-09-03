from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.supplier_payment import (
    SupplierPaymentCreate,
    SupplierPaymentResponse,
    SupplierBalanceSummary,
    SupplierLedgerResponse,
    SupplierCreditApplicationCreate,
    SupplierCreditApplicationResponse,
)

from app.crud.supplier_payment import (
    create_supplier_payment,
    get_purchase_payments,
    get_supplier_payments,
    get_all_supplier_payments,
    get_supplier_balance_summary,
    get_supplier_ledger,
    apply_supplier_credit,
    get_purchase_credit_applications,
    get_all_credit_applications,
    get_all_supplier_dues,
)


router = APIRouter(
    prefix="/supplier-payment",
    tags=["Supplier Payment"],
)


# ==========================================================
# CREATE SUPPLIER PAYMENT
# ==========================================================

@router.post(
    "/create",
    response_model=SupplierPaymentResponse,
)
def create_supplier_payment_api(
    data: SupplierPaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_supplier_payment(
        db=db,
        shop_id=current_user.shop_id,
        data=data,
    )


# ==========================================================
# ALL SUPPLIER DUES
# ==========================================================

@router.get(
    "/dues",
)
def supplier_due_list(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_supplier_dues(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# ALL SUPPLIER PAYMENTS
# ==========================================================

@router.get(
    "/",
    response_model=list[SupplierPaymentResponse],
)
def supplier_payment_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_supplier_payments(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# PAYMENTS FOR PURCHASE
# ==========================================================

@router.get(
    "/purchase/{purchase_id}",
    response_model=list[SupplierPaymentResponse],
)
def purchase_payment_history(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_purchase_payments(
        db=db,
        shop_id=current_user.shop_id,
        purchase_id=purchase_id,
    )


# ==========================================================
# PAYMENTS FOR SUPPLIER
# ==========================================================

@router.get(
    "/supplier/{supplier_id}",
    response_model=list[SupplierPaymentResponse],
)
def supplier_payment_history(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_supplier_payments(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )


# ==========================================================
# SUPPLIER BALANCE SUMMARY
# ==========================================================

@router.get(
    "/supplier/{supplier_id}/summary",
    response_model=SupplierBalanceSummary,
)
def supplier_balance_summary(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_supplier_balance_summary(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )


# ==========================================================
# SUPPLIER LEDGER
# ==========================================================

@router.get(
    "/supplier/{supplier_id}/ledger",
    response_model=SupplierLedgerResponse,
)
def supplier_ledger(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_supplier_ledger(
        db=db,
        shop_id=current_user.shop_id,
        supplier_id=supplier_id,
    )


# ==========================================================
# APPLY SUPPLIER CREDIT TO PURCHASE
# ==========================================================

@router.post(
    "/credit/apply",
    response_model=SupplierCreditApplicationResponse,
)
def apply_credit_to_purchase(
    data: SupplierCreditApplicationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return apply_supplier_credit(
        db=db,
        shop_id=current_user.shop_id,
        data=data,
    )


# ==========================================================
# CREDIT APPLICATIONS FOR PURCHASE
# ==========================================================

@router.get(
    "/credit/purchase/{purchase_id}",
    response_model=list[SupplierCreditApplicationResponse],
)
def purchase_credit_history(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_purchase_credit_applications(
        db=db,
        shop_id=current_user.shop_id,
        purchase_id=purchase_id,
    )


# ==========================================================
# ALL CREDIT APPLICATIONS
# ==========================================================

@router.get(
    "/credit",
    response_model=list[SupplierCreditApplicationResponse],
)
def all_credit_applications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_all_credit_applications(
        db=db,
        shop_id=current_user.shop_id,
    )
