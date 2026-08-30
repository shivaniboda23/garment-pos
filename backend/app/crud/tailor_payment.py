from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.supplier import Supplier
from app.models.tailoring_job import TailoringJob
from app.models.tailor_payment import TailorPayment
from app.schemas.tailor_payment import TailorPaymentCreate


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _supplier_type(supplier: Supplier) -> str:
    return str(
        getattr(supplier, "supplier_type", "SUPPLIER")
        or "SUPPLIER"
    ).strip().upper()


def _validate_tailor(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active.is_(True),
        )
        .first()
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Tailor not found.",
        )

    if _supplier_type(supplier) not in ("TAILOR", "BOTH"):
        raise HTTPException(
            status_code=400,
            detail="Selected supplier is not configured as a TAILOR or BOTH.",
        )

    return supplier


def _job_paid_amount(
    db: Session,
    shop_id: int,
    job_id: int,
) -> Decimal:
    value = (
        db.query(
            func.coalesce(
                func.sum(TailorPayment.amount),
                0,
            )
        )
        .filter(
            TailorPayment.shop_id == shop_id,
            TailorPayment.tailoring_job_id == job_id,
        )
        .scalar()
    )
    return _money(value)


def _payment_status(charge: Decimal, paid: Decimal) -> str:
    if charge <= 0:
        return "No Charge"
    if paid <= 0:
        return "Unpaid"
    if paid >= charge:
        return "Paid"
    return "Partial"


def create_tailor_payment(
    db: Session,
    shop_id: int,
    data: TailorPaymentCreate,
):
    job = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.id == data.tailoring_job_id,
            TailoringJob.shop_id == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tailoring job not found.",
        )

    if job.status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cannot pay a cancelled tailoring job.",
        )

    supplier = _validate_tailor(
        db=db,
        shop_id=shop_id,
        supplier_id=job.supplier_id,
    )

    charge = _money(job.stitching_charge)
    paid = _job_paid_amount(
        db=db,
        shop_id=shop_id,
        job_id=job.id,
    )

    if charge <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "This tailoring job has no stitching charge. "
                "Set the stitching charge before recording payment."
            ),
        )

    remaining = charge - paid

    if remaining <= 0:
        raise HTTPException(
            status_code=400,
            detail="This tailoring job is already fully paid.",
        )

    amount = _money(data.amount)

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero.",
        )

    if amount > remaining:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment amount ₹{amount} exceeds "
                f"remaining tailor due ₹{remaining}."
            ),
        )

    try:
        payment = TailorPayment(
            shop_id=shop_id,
            supplier_id=supplier.id,
            tailoring_job_id=job.id,
            amount=amount,
            payment_method=data.payment_method.strip(),
            reference_number=data.reference_number,
            notes=data.notes,
        )

        if data.payment_date is not None:
            payment.payment_date = data.payment_date

        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def get_all_tailor_payments(
    db: Session,
    shop_id: int,
):
    return (
        db.query(TailorPayment)
        .filter(TailorPayment.shop_id == shop_id)
        .order_by(
            TailorPayment.payment_date.desc(),
            TailorPayment.id.desc(),
        )
        .all()
    )


def get_job_payments(
    db: Session,
    shop_id: int,
    job_id: int,
):
    job = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.id == job_id,
            TailoringJob.shop_id == shop_id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tailoring job not found.",
        )

    return (
        db.query(TailorPayment)
        .filter(
            TailorPayment.shop_id == shop_id,
            TailorPayment.tailoring_job_id == job_id,
        )
        .order_by(
            TailorPayment.payment_date.asc(),
            TailorPayment.id.asc(),
        )
        .all()
    )


def get_tailor_payments(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    _validate_tailor(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
    )

    return (
        db.query(TailorPayment)
        .filter(
            TailorPayment.shop_id == shop_id,
            TailorPayment.supplier_id == supplier_id,
        )
        .order_by(
            TailorPayment.payment_date.desc(),
            TailorPayment.id.desc(),
        )
        .all()
    )


def get_job_payment_summary(
    db: Session,
    shop_id: int,
    job_id: int,
):
    job = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.id == job_id,
            TailoringJob.shop_id == shop_id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tailoring job not found.",
        )

    supplier = job.supplier
    bill = job.bill
    variant = job.variant

    product_name = ""
    try:
        if variant and variant.product:
            product_name = variant.product.product_name or ""
    except Exception:
        product_name = ""

    payments = get_job_payments(
        db=db,
        shop_id=shop_id,
        job_id=job.id,
    )

    charge = _money(job.stitching_charge)
    paid = sum(
        (_money(payment.amount) for payment in payments),
        Decimal("0.00"),
    )
    due = max(Decimal("0.00"), charge - paid)

    return {
        "tailoring_job_id": job.id,
        "job_number": job.job_number,
        "supplier_id": job.supplier_id,
        "supplier_name": supplier.supplier_name if supplier else "",
        "invoice_number": bill.invoice_number if bill else "",
        "product_name": product_name,
        "quantity": int(job.quantity or 0),
        "stitching_charge": charge,
        "paid_amount": paid,
        "due_amount": due,
        "payment_status": _payment_status(charge, paid),
        "payments": payments,
    }


def get_tailor_balance_summary(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = _validate_tailor(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
    )

    jobs = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.shop_id == shop_id,
            TailoringJob.supplier_id == supplier_id,
            TailoringJob.status != "Cancelled",
        )
        .all()
    )

    payments = get_tailor_payments(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
    )

    total_charges = sum(
        (_money(job.stitching_charge) for job in jobs),
        Decimal("0.00"),
    )
    total_paid = sum(
        (_money(payment.amount) for payment in payments),
        Decimal("0.00"),
    )
    payable = max(Decimal("0.00"), total_charges - total_paid)

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "total_jobs": len(jobs),
        "total_agreed_charges": total_charges,
        "total_paid": total_paid,
        "payable": payable,
    }


def get_all_tailor_dues(
    db: Session,
    shop_id: int,
):
    jobs = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.shop_id == shop_id,
            TailoringJob.status != "Cancelled",
            TailoringJob.stitching_charge > 0,
        )
        .order_by(
            TailoringJob.assigned_at.asc(),
            TailoringJob.id.asc(),
        )
        .all()
    )

    results = []

    for job in jobs:
        charge = _money(job.stitching_charge)
        paid = _job_paid_amount(
            db=db,
            shop_id=shop_id,
            job_id=job.id,
        )
        due = charge - paid

        if due <= 0:
            continue

        supplier = job.supplier
        bill = job.bill
        customer = job.customer
        variant = job.variant

        product_name = ""
        try:
            if variant and variant.product:
                product_name = variant.product.product_name or ""
        except Exception:
            product_name = ""

        results.append(
            {
                "tailoring_job_id": job.id,
                "job_number": job.job_number,
                "supplier_id": job.supplier_id,
                "supplier_name": supplier.supplier_name if supplier else "",
                "invoice_number": bill.invoice_number if bill else "",
                "product_name": product_name,
                "customer_name": customer.customer_name if customer else "",
                "stitching_charge": charge,
                "paid_amount": paid,
                "due_amount": due,
                "job_status": job.status,
                "assigned_at": job.assigned_at,
            }
        )

    return results


def get_tailor_ledger(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    supplier = _validate_tailor(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
    )

    jobs = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.shop_id == shop_id,
            TailoringJob.supplier_id == supplier_id,
            TailoringJob.status != "Cancelled",
            TailoringJob.stitching_charge > 0,
        )
        .all()
    )

    payments = get_tailor_payments(
        db=db,
        shop_id=shop_id,
        supplier_id=supplier_id,
    )

    transactions = []

    for job in jobs:
        transactions.append(
            {
                "date": job.assigned_at,
                "transaction_type": "Tailoring Charge",
                "reference": job.job_number,
                "debit": _money(job.stitching_charge),
                "credit": Decimal("0.00"),
                "id": job.id,
                "priority": 1,
            }
        )

    for payment in payments:
        transactions.append(
            {
                "date": payment.payment_date,
                "transaction_type": "Tailor Payment",
                "reference": payment.reference_number or f"TPAY-{payment.id}",
                "debit": Decimal("0.00"),
                "credit": _money(payment.amount),
                "id": payment.id,
                "priority": 2,
            }
        )

    transactions.sort(
        key=lambda item: (
            item["date"],
            item["priority"],
            item["id"],
        )
    )

    running_balance = Decimal("0.00")
    entries = []

    for transaction in transactions:
        running_balance += transaction["debit"] - transaction["credit"]
        entries.append(
            {
                "date": transaction["date"],
                "transaction_type": transaction["transaction_type"],
                "reference": transaction["reference"],
                "debit": transaction["debit"],
                "credit": transaction["credit"],
                "balance": running_balance,
            }
        )

    total_charges = sum(
        (_money(job.stitching_charge) for job in jobs),
        Decimal("0.00"),
    )
    total_paid = sum(
        (_money(payment.amount) for payment in payments),
        Decimal("0.00"),
    )

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "entries": entries,
        "total_agreed_charges": total_charges,
        "total_paid": total_paid,
        "payable": max(Decimal("0.00"), total_charges - total_paid),
    }
