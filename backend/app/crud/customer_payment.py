from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.customer import Customer
from app.models.payment import Payment

from app.schemas.customer_payment import (
    CustomerPaymentCreate,
)
from app.services.customer_receivable import (
    ZERO,
    calculate_bill_receivable,
    get_bill_receivable,
)


ACCOUNTING_ERROR = (
    "Customer receivable accounting integrity check failed."
)


def _get_bill_receivable_or_500(
    db: Session,
    shop_id: int,
    bill: Bill,
):
    try:
        return get_bill_receivable(
            db=db,
            shop_id=shop_id,
            bill=bill,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=ACCOUNTING_ERROR,
        ) from exc


# ==========================================================
# CREATE CUSTOMER PAYMENT
# ==========================================================

def create_customer_payment(
    db: Session,
    shop_id: int,
    data: CustomerPaymentCreate,
):
    bill = (
        db.query(Bill)
        .filter(
            Bill.id == data.bill_id,
            Bill.shop_id == shop_id,
        )
        .with_for_update(of=Bill)
        .first()
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found.",
        )

    if bill.customer_id is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "This bill does not have a customer."
            ),
        )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == bill.customer_id,
            Customer.shop_id == shop_id,
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    state = _get_bill_receivable_or_500(
        db=db,
        shop_id=shop_id,
        bill=bill,
    )

    amount = Decimal(
        str(data.amount)
    )

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Payment amount must be greater than zero."
            ),
        )

    if state.due <= ZERO:
        raise HTTPException(
            status_code=400,
            detail=(
                "This bill has no outstanding balance."
            ),
        )

    if amount > state.due:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount ₹{amount:.2f} "
                f"exceeds outstanding balance "
                f"₹{state.due:.2f}."
            ),
        )

    try:

        payment = Payment(
            bill_id=bill.id,
            amount=amount,
            payment_method=data.payment_method,
            transaction_reference=(
                data.transaction_reference
            ),
        )

        db.add(payment)

        new_state = calculate_bill_receivable(
            original_total=state.original_total,
            payments=state.payments + amount,
            completed_returns=state.completed_returns,
        )
        bill.payment_status = new_state.payment_status

        db.commit()

        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


# ==========================================================
# BILL PAYMENT HISTORY
# ==========================================================

def get_bill_payments(
    db: Session,
    shop_id: int,
    bill_id: int,
):
    bill = (
        db.query(Bill)
        .filter(
            Bill.id == bill_id,
            Bill.shop_id == shop_id,
        )
        .first()
    )

    if not bill:
        raise HTTPException(
            status_code=404,
            detail="Bill not found.",
        )

    return (
        db.query(Payment)
        .filter(
            Payment.bill_id == bill_id,
        )
        .order_by(
            Payment.id.desc(),
        )
        .all()
    )


# ==========================================================
# CUSTOMER DUE SUMMARY
# ==========================================================

def get_customer_due_summary(
    db: Session,
    shop_id: int,
    customer_id: int,
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.shop_id == shop_id,
            Customer.is_active == True,
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    bills = (
        db.query(Bill)
        .filter(
            Bill.shop_id == shop_id,
            Bill.customer_id == customer_id,
        )
        .order_by(
            Bill.created_at.desc(),
            Bill.id.desc(),
        )
        .all()
    )

    invoice_rows = []
    refundable_rows = []

    total_billed = ZERO
    total_returns = ZERO
    total_effective_obligation = ZERO
    total_paid = ZERO
    total_due = ZERO
    total_refundable_entitlement = ZERO

    for bill in bills:
        state = _get_bill_receivable_or_500(
            db=db,
            shop_id=shop_id,
            bill=bill,
        )

        total_billed += state.original_total
        total_returns += state.completed_returns
        total_effective_obligation += (
            state.effective_obligation
        )
        total_paid += state.payments
        total_due += state.due
        total_refundable_entitlement += (
            state.refundable_entitlement
        )

        if state.due > ZERO:
            invoice_rows.append(
                {
                    "bill_id": bill.id,
                    "invoice_number": bill.invoice_number,
                    "grand_total": state.original_total,
                    "paid_amount": state.payments,
                    "due_amount": state.due,
                    "payment_status": state.payment_status,
                    "returned_amount": state.completed_returns,
                    "effective_obligation": (
                        state.effective_obligation
                    ),
                    "refundable_entitlement": (
                        state.refundable_entitlement
                    ),
                    "created_at": bill.created_at,
                }
            )

        if state.refundable_entitlement > ZERO:
            refundable_rows.append(
                {
                    "bill_id": bill.id,
                    "invoice_number": bill.invoice_number,
                    "grand_total": state.original_total,
                    "returned_amount": state.completed_returns,
                    "effective_obligation": (
                        state.effective_obligation
                    ),
                    "paid_amount": state.payments,
                    "refundable_entitlement": (
                        state.refundable_entitlement
                    ),
                    "payment_status": state.payment_status,
                    "created_at": bill.created_at,
                }
            )

    return {
        "customer_id":
            customer.id,

        "customer_name":
            customer.customer_name,

        "total_billed":
            total_billed,

        "total_returns":
            total_returns,

        "total_effective_obligation":
            total_effective_obligation,

        "total_paid":
            total_paid,

        "total_due":
            total_due,

        "total_refundable_entitlement":
            total_refundable_entitlement,

        "bills":
            invoice_rows,

        "refundable_bills":
            refundable_rows,
    }


# ==========================================================
# ALL CUSTOMER DUES
# ==========================================================

def get_all_customer_dues(
    db: Session,
    shop_id: int,
):
    customers = (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id,
            Customer.is_active == True,
        )
        .order_by(
            Customer.customer_name.asc(),
        )
        .all()
    )

    results = []

    for customer in customers:

        bills = (
            db.query(Bill)
            .filter(
                Bill.shop_id == shop_id,
                Bill.customer_id
                == customer.id,
            )
            .all()
        )

        total_billed = ZERO
        total_returns = ZERO
        total_effective_obligation = ZERO
        total_paid = ZERO
        total_due = ZERO
        total_refundable_entitlement = ZERO

        for bill in bills:
            state = _get_bill_receivable_or_500(
                db=db,
                shop_id=shop_id,
                bill=bill,
            )

            total_billed += state.original_total
            total_returns += state.completed_returns
            total_effective_obligation += (
                state.effective_obligation
            )
            total_paid += state.payments
            total_due += state.due
            total_refundable_entitlement += (
                state.refundable_entitlement
            )

        # Only actual outstanding customers
        # appear in this endpoint.
        if total_due <= ZERO:
            continue

        results.append(
            {
                "customer_id":
                    customer.id,

                "customer_name":
                    customer.customer_name,

                "phone":
                    customer.phone,

                "total_billed":
                    total_billed,

                "total_returns":
                    total_returns,

                "total_effective_obligation":
                    total_effective_obligation,

                "total_paid":
                    total_paid,

                "total_due":
                    total_due,

                "total_refundable_entitlement":
                    total_refundable_entitlement,
            }
        )

    return results
