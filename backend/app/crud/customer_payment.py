from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.customer import Customer
from app.models.payment import Payment

from app.schemas.customer_payment import (
    CustomerPaymentCreate,
)


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

    total_paid = (
        db.query(
            func.coalesce(
                func.sum(
                    Payment.amount
                ),
                0,
            )
        )
        .filter(
            Payment.bill_id == bill.id,
        )
        .scalar()
    )

    total_paid = Decimal(
        str(
            total_paid or 0
        )
    )

    grand_total = Decimal(
        str(
            bill.grand_total or 0
        )
    )

    current_due = (
        grand_total
        - total_paid
    )

    if current_due < 0:
        current_due = Decimal(
            "0.00"
        )

    if current_due <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "This bill has no outstanding balance."
            ),
        )

    if amount > current_due:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount ₹{amount:.2f} "
                f"exceeds outstanding balance "
                f"₹{current_due:.2f}."
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

        new_paid = (
            total_paid
            + amount
        )

        new_due = (
            grand_total
            - new_paid
        )

        if new_due < 0:
            new_due = Decimal(
                "0.00"
            )

        if new_paid >= grand_total:
            bill.payment_status = "Paid"
        elif new_paid > 0:
            bill.payment_status = "Partial"
        else:
            bill.payment_status = "Pending"

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

    total_billed = Decimal("0.00")
    total_paid = Decimal("0.00")
    total_due = Decimal("0.00")

    for bill in bills:

        paid = (
            db.query(
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ),
                    0,
                )
            )
            .filter(
                Payment.bill_id == bill.id,
            )
            .scalar()
        )

        paid = Decimal(
            str(
                paid or 0
            )
        )

        grand_total = Decimal(
            str(
                bill.grand_total or 0
            )
        )

        due = (
            grand_total
            - paid
        )

        if due < 0:
            due = Decimal(
                "0.00"
            )

        total_billed += grand_total
        total_paid += paid
        total_due += due

        if due > 0:
            invoice_rows.append(
                {
                    "bill_id":
                        bill.id,
                    "invoice_number":
                        bill.invoice_number,
                    "grand_total":
                        grand_total,
                    "paid_amount":
                        paid,
                    "due_amount":
                        due,
                    "payment_status":
                        "Pending",
                    "created_at":
                        bill.created_at,
                }
            )

    return {
        "customer_id":
            customer.id,

        "customer_name":
            customer.customer_name,

        "total_billed":
            total_billed,

        "total_paid":
            total_paid,

        "total_due":
            total_due,

        "bills":
            invoice_rows,
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

        total_billed = Decimal(
            "0.00"
        )

        total_paid = Decimal(
            "0.00"
        )

        total_due = Decimal(
            "0.00"
        )

        for bill in bills:

            paid = (
                db.query(
                    func.coalesce(
                        func.sum(
                            Payment.amount
                        ),
                        0,
                    )
                )
                .filter(
                    Payment.bill_id
                    == bill.id,
                )
                .scalar()
            )

            paid = Decimal(
                str(
                    paid or 0
                )
            )

            grand_total = Decimal(
                str(
                    bill.grand_total
                    or 0
                )
            )

            due = (
                grand_total
                - paid
            )

            if due < 0:
                due = Decimal(
                    "0.00"
                )

            total_billed += (
                grand_total
            )

            total_paid += (
                paid
            )

            total_due += (
                due
            )

        # Only actual outstanding customers
        # appear in this endpoint.
        if total_due <= 0:
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

                "total_paid":
                    total_paid,

                "total_due":
                    total_due,
            }
        )

    return results
