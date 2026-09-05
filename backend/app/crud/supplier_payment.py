from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn
from app.models.supplier import Supplier
from app.models.supplier_payment import SupplierPayment
from app.models.supplier_credit_application import (
    SupplierCreditApplication,
)
from app.schemas.supplier_payment import (
    SupplierPaymentCreate,
    SupplierCreditApplicationCreate,
)
from app.services.supplier_accounting import (
    get_purchase_accounting,
    get_supplier_accounting,
)


# ==========================================================
# CREATE SUPPLIER PAYMENT
# ==========================================================

def create_supplier_payment(
    db: Session,
    shop_id: int,
    data: SupplierPaymentCreate,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == data.supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.id == data.purchase_id,
            Purchase.shop_id == shop_id,
        )
        .with_for_update(of=Purchase)
        .first()
    )

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found.",
        )

    if purchase.supplier_id != supplier.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Selected supplier does not match "
                "the supplier of this purchase."
            ),
        )

    amount = Decimal(str(data.amount))

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero.",
        )

    current_balance = get_purchase_accounting(
        db=db,
        shop_id=shop_id,
        purchase=purchase,
    ).effective_due

    if current_balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="This purchase has no outstanding balance.",
        )

    if amount > current_balance:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount ₹{amount} exceeds "
                f"outstanding balance ₹{current_balance}."
            ),
        )

    try:
        payment = SupplierPayment(
            shop_id=shop_id,
            supplier_id=supplier.id,
            purchase_id=purchase.id,
            amount=amount,
            payment_method=data.payment_method,
            reference_number=data.reference_number,
            notes=data.notes,
        )

        if data.payment_date is not None:
            payment.payment_date = data.payment_date

        db.add(payment)

        current_paid = Decimal(
            str(purchase.paid_amount or 0)
        )

        new_paid = current_paid + amount

        new_balance = max(
            current_balance - amount,
            Decimal("0.00"),
        )

        purchase.paid_amount = new_paid
        purchase.balance_amount = new_balance

        purchase.status = (
            "Completed"
            if new_balance == 0
            else "Pending"
        )

        db.commit()
        db.refresh(payment)

        return payment

    except Exception:
        db.rollback()
        raise


# ==========================================================
# APPLY SUPPLIER CREDIT
# ==========================================================

def apply_supplier_credit(
    db: Session,
    shop_id: int,
    data: SupplierCreditApplicationCreate,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == data.supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .with_for_update(of=Supplier)
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.id == data.purchase_id,
            Purchase.shop_id == shop_id,
        )
        .with_for_update(of=Purchase)
        .first()
    )

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found.",
        )

    if purchase.supplier_id != supplier.id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Selected supplier does not match "
                "the selected purchase."
            ),
        )

    amount = Decimal(str(data.amount))

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Credit application amount must "
                "be greater than zero."
            ),
        )

    current_balance = get_purchase_accounting(
        db=db,
        shop_id=shop_id,
        purchase=purchase,
    ).effective_due

    if current_balance <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "This purchase has no outstanding "
                "balance."
            ),
        )

    if amount > current_balance:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Credit application ₹{amount} "
                f"exceeds purchase outstanding "
                f"₹{current_balance}."
            ),
        )

    supplier_accounting = get_supplier_accounting(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier.id,
        opening_balance=supplier.opening_balance,
    )

    available_credit = (
        supplier_accounting.unallocated_credit
    )

    if amount > available_credit:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Credit application ₹{amount} "
                f"exceeds available supplier credit "
                f"₹{available_credit}."
            ),
        )

    application = SupplierCreditApplication(
        shop_id=shop_id,
        supplier_id=supplier.id,
        purchase_id=purchase.id,
        amount=amount,
        reference_number=data.reference_number,
        notes=data.notes,
    )

    if data.applied_at is not None:
        application.applied_at = data.applied_at

    db.add(application)

    current_paid = Decimal(
        str(
            purchase.paid_amount or 0
        )
    )

    new_paid = current_paid + amount

    new_balance = current_balance - amount

    if new_balance < 0:
        new_balance = Decimal("0.00")

    purchase.paid_amount = new_paid
    purchase.balance_amount = new_balance

    purchase.status = (
        "Completed"
        if new_balance == 0
        else "Pending"
    )

    try:
        db.commit()
        db.refresh(application)

        return application

    except Exception:
        db.rollback()
        raise


# ==========================================================
# GET CREDIT APPLICATIONS FOR PURCHASE
# ==========================================================

def get_purchase_credit_applications(
    db: Session,
    shop_id: int,
    purchase_id: int,
):
    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.id == purchase_id,
            Purchase.shop_id == shop_id,
        )
        .first()
    )

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found.",
        )

    return (
        db.query(
            SupplierCreditApplication
        )
        .filter(
            SupplierCreditApplication.shop_id == shop_id,
            SupplierCreditApplication.purchase_id
            == purchase_id,
        )
        .order_by(
            SupplierCreditApplication.applied_at.desc(),
            SupplierCreditApplication.id.desc(),
        )
        .all()
    )


# ==========================================================
# GET ALL CREDIT APPLICATIONS
# ==========================================================

def get_all_credit_applications(
    db: Session,
    shop_id: int,
):
    return (
        db.query(
            SupplierCreditApplication
        )
        .filter(
            SupplierCreditApplication.shop_id == shop_id,
        )
        .order_by(
            SupplierCreditApplication.applied_at.desc(),
            SupplierCreditApplication.id.desc(),
        )
        .all()
    )


# ==========================================================
# GET PAYMENTS FOR PURCHASE
# ==========================================================

def get_purchase_payments(
    db: Session,
    shop_id: int,
    purchase_id: int,
):
    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.id == purchase_id,
            Purchase.shop_id == shop_id,
        )
        .first()
    )

    if not purchase:
        raise HTTPException(
            status_code=404,
            detail="Purchase not found.",
        )

    return (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.purchase_id == purchase_id,
        )
        .order_by(
            SupplierPayment.payment_date.desc(),
            SupplierPayment.id.desc(),
        )
        .all()
    )


# ==========================================================
# GET SUPPLIER PAYMENTS
# ==========================================================

def get_supplier_payments(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    return (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.supplier_id == supplier_id,
        )
        .order_by(
            SupplierPayment.payment_date.desc(),
            SupplierPayment.id.desc(),
        )
        .all()
    )


# ==========================================================
# GET ALL PAYMENTS
# ==========================================================

def get_all_supplier_payments(
    db: Session,
    shop_id: int,
):
    return (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.shop_id == shop_id,
        )
        .order_by(
            SupplierPayment.payment_date.desc(),
            SupplierPayment.id.desc(),
        )
        .all()
    )


# ==========================================================
# SUPPLIER BALANCE SUMMARY
# ==========================================================

def get_supplier_balance_summary(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    opening_balance = Decimal(
        str(
            supplier.opening_balance or 0
        )
    )
    accounting = get_supplier_accounting(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
        opening_balance=opening_balance,
    )

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "opening_balance": opening_balance,
        "total_purchases": accounting.total_purchases,
        "total_purchase_returns": accounting.total_purchase_returns,
        "total_payments": accounting.total_payments,
        "total_credit_applied": accounting.total_credit_applied,
        "payable": accounting.payable,
        "supplier_credit": accounting.unallocated_credit,
        "net_position": accounting.net_position,
        "transaction_outstanding": accounting.payable,
    }


# ==========================================================
# ALL SUPPLIER DUES
# ==========================================================

def get_all_supplier_dues(
    db: Session,
    shop_id: int,
):
    purchases = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
        )
        .order_by(
            Purchase.created_at.desc(),
            Purchase.id.desc(),
        )
        .all()
    )

    results = []

    for purchase in purchases:
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id
                == purchase.supplier_id,
                Supplier.shop_id
                == shop_id,
            )
            .first()
        )

        if not supplier:
            continue

        balance = get_purchase_accounting(
            db=db,
            shop_id=shop_id,
            purchase=purchase,
        ).effective_due

        if balance <= 0:
            continue

        results.append(
            {
                "purchase_id":
                    purchase.id,
                "invoice_number":
                    purchase.invoice_number,
                "supplier_id":
                    supplier.id,
                "supplier_name":
                    supplier.supplier_name,
                "grand_total":
                    Decimal(
                        str(
                            purchase.grand_total
                            or 0
                        )
                    ),
                "paid_amount":
                    Decimal(
                        str(
                            purchase.paid_amount
                            or 0
                        )
                    ),
                "due_amount":
                    balance,
                "created_at":
                    purchase.created_at,
            }
        )

    return results


# ==========================================================
# SUPPLIER LEDGER
# ==========================================================

def get_supplier_ledger(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found.",
        )

    purchases = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
            Purchase.supplier_id == supplier_id,
        )
        .order_by(
            Purchase.created_at.asc(),
            Purchase.id.asc(),
        )
        .all()
    )

    purchase_returns = (
        db.query(PurchaseReturn)
        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.supplier_id == supplier_id,
            PurchaseReturn.status == "Completed",
        )
        .order_by(
            PurchaseReturn.created_at.asc(),
            PurchaseReturn.id.asc(),
        )
        .all()
    )

    payments = (
        db.query(SupplierPayment)
        .filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.supplier_id == supplier_id,
        )
        .order_by(
            SupplierPayment.payment_date.asc(),
            SupplierPayment.id.asc(),
        )
        .all()
    )

    credit_applications = (
        db.query(
            SupplierCreditApplication
        )
        .filter(
            SupplierCreditApplication.shop_id == shop_id,
            SupplierCreditApplication.supplier_id
            == supplier_id,
        )
        .order_by(
            SupplierCreditApplication.applied_at.asc(),
            SupplierCreditApplication.id.asc(),
        )
        .all()
    )

    transactions = []

    priority = {
        "Purchase": 1,
        "Purchase Return": 2,
        "Payment": 3,
        "Credit Application": 4,
    }

    for purchase in purchases:
        transactions.append(
            {
                "date": purchase.created_at,
                "transaction_type": "Purchase",
                "reference": purchase.invoice_number,
                "debit": Decimal(
                    str(
                        purchase.grand_total
                        or 0
                    )
                ),
                "credit": Decimal("0.00"),
                "id": purchase.id,
                "priority": priority["Purchase"],
            }
        )

    for purchase_return in purchase_returns:
        transactions.append(
            {
                "date": purchase_return.created_at,
                "transaction_type": "Purchase Return",
                "reference": purchase_return.return_number,
                "debit": Decimal("0.00"),
                "credit": Decimal(
                    str(
                        purchase_return.total_amount
                        or 0
                    )
                ),
                "id": purchase_return.id,
                "priority": priority["Purchase Return"],
            }
        )

    for payment in payments:
        transactions.append(
            {
                "date": payment.payment_date,
                "transaction_type": "Payment",
                "reference": (
                    payment.reference_number
                    or f"PAY-{payment.id}"
                ),
                "debit": Decimal("0.00"),
                "credit": Decimal(
                    str(
                        payment.amount
                        or 0
                    )
                ),
                "id": payment.id,
                "priority": priority["Payment"],
            }
        )

    for application in credit_applications:
        transactions.append(
            {
                "date": application.applied_at,
                "transaction_type": "Credit Application",
                "reference": (
                    application.reference_number
                    or f"CREDIT-{application.id}"
                ),
                "debit": Decimal(
                    str(
                        application.amount
                        or 0
                    )
                ),
                "credit": Decimal(
                    str(
                        application.amount
                        or 0
                    )
                ),
                "id": application.id,
                "priority": priority[
                    "Credit Application"
                ],
            }
        )

    transactions.sort(
        key=lambda transaction: (
            transaction["date"],
            transaction["priority"],
            transaction["id"],
        )
    )

    running_balance = Decimal(
        str(supplier.opening_balance or 0)
    )
    entries = []

    for transaction in transactions:

        running_balance += (
            transaction["debit"]
            - transaction["credit"]
        )

        entries.append(
            {
                "date":
                    transaction["date"],

                "transaction_type":
                    transaction[
                        "transaction_type"
                    ],

                "reference":
                    transaction[
                        "reference"
                    ],

                "debit":
                    transaction[
                        "debit"
                    ],

                "credit":
                    transaction[
                        "credit"
                    ],

                "balance":
                    running_balance,
            }
        )

    accounting = get_supplier_accounting(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
        opening_balance=supplier.opening_balance,
    )

    return {
        "supplier_id":
            supplier.id,

        "supplier_name":
            supplier.supplier_name,

        "opening_balance":
            Decimal(
                str(
                    supplier.opening_balance
                    or 0
                )
            ),

        "entries":
            entries,

        "payable":
            accounting.payable,

        "supplier_credit":
            accounting.unallocated_credit,

        "net_position":
            accounting.net_position,

        "transaction_outstanding":
            accounting.payable,
    }
