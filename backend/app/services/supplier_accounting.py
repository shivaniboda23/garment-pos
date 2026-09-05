from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn
from app.models.supplier_credit_application import (
    SupplierCreditApplication,
)
from app.models.supplier_payment import SupplierPayment


ZERO = Decimal("0.00")


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0))


@dataclass(frozen=True)
class PurchaseAccounting:
    grand_total: Decimal
    cash_payments: Decimal
    completed_returns: Decimal
    credit_applications: Decimal
    raw_position: Decimal
    effective_due: Decimal
    generated_credit: Decimal
    credit_consumed: Decimal


@dataclass(frozen=True)
class SupplierAccounting:
    total_purchases: Decimal
    total_purchase_returns: Decimal
    total_payments: Decimal
    total_credit_applied: Decimal
    payable: Decimal
    unallocated_credit: Decimal
    net_position: Decimal


def get_purchase_accounting(
    db: Session,
    shop_id: int,
    purchase: Purchase,
) -> PurchaseAccounting:
    if purchase.shop_id != shop_id:
        raise ValueError("Purchase not found.")

    cash_payments = _decimal(
        db.query(
            func.coalesce(
                func.sum(SupplierPayment.amount),
                0,
            )
        )
        .filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.purchase_id == purchase.id,
            SupplierPayment.supplier_id == purchase.supplier_id,
        )
        .scalar()
    )

    completed_returns = _decimal(
        db.query(
            func.coalesce(
                func.sum(PurchaseReturn.total_amount),
                0,
            )
        )
        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.purchase_id == purchase.id,
            PurchaseReturn.supplier_id == purchase.supplier_id,
            PurchaseReturn.status == "Completed",
        )
        .scalar()
    )

    credit_applications = _decimal(
        db.query(
            func.coalesce(
                func.sum(SupplierCreditApplication.amount),
                0,
            )
        )
        .filter(
            SupplierCreditApplication.shop_id == shop_id,
            SupplierCreditApplication.purchase_id == purchase.id,
            SupplierCreditApplication.supplier_id
            == purchase.supplier_id,
        )
        .scalar()
    )

    grand_total = _decimal(purchase.grand_total)
    raw_position = (
        grand_total
        - cash_payments
        - completed_returns
    )
    purchase_due_before_credit = max(raw_position, ZERO)
    generated_credit = max(-raw_position, ZERO)
    credit_consumed = min(
        credit_applications,
        purchase_due_before_credit,
    )
    effective_due = max(
        raw_position - credit_applications,
        ZERO,
    )

    return PurchaseAccounting(
        grand_total=grand_total,
        cash_payments=cash_payments,
        completed_returns=completed_returns,
        credit_applications=credit_applications,
        raw_position=raw_position,
        effective_due=effective_due,
        generated_credit=generated_credit,
        credit_consumed=credit_consumed,
    )


def get_supplier_accounting(
    db: Session,
    shop_id: int,
    supplier_id: int,
    opening_balance,
) -> SupplierAccounting:
    purchases = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
            Purchase.supplier_id == supplier_id,
        )
        .all()
    )

    purchase_totals = [
        get_purchase_accounting(
            db=db,
            shop_id=shop_id,
            purchase=purchase,
        )
        for purchase in purchases
    ]

    opening_balance = _decimal(opening_balance)
    opening_payable = max(opening_balance, ZERO)
    opening_credit = max(-opening_balance, ZERO)

    total_purchases = sum(
        (item.grand_total for item in purchase_totals),
        ZERO,
    )
    total_purchase_returns = sum(
        (item.completed_returns for item in purchase_totals),
        ZERO,
    )
    total_payments = sum(
        (item.cash_payments for item in purchase_totals),
        ZERO,
    )
    total_credit_applied = sum(
        (item.credit_applications for item in purchase_totals),
        ZERO,
    )
    payable = opening_payable + sum(
        (item.effective_due for item in purchase_totals),
        ZERO,
    )
    unallocated_credit = max(
        opening_credit
        + sum(
            (item.generated_credit for item in purchase_totals),
            ZERO,
        )
        - sum(
            (item.credit_consumed for item in purchase_totals),
            ZERO,
        ),
        ZERO,
    )

    return SupplierAccounting(
        total_purchases=total_purchases,
        total_purchase_returns=total_purchase_returns,
        total_payments=total_payments,
        total_credit_applied=total_credit_applied,
        payable=payable,
        unallocated_credit=unallocated_credit,
        net_position=payable - unallocated_credit,
    )


def sync_purchase_balance(
    db: Session,
    shop_id: int,
    purchase: Purchase,
) -> Decimal:
    effective_due = get_purchase_accounting(
        db=db,
        shop_id=shop_id,
        purchase=purchase,
    ).effective_due

    purchase.balance_amount = effective_due
    purchase.status = (
        "Completed"
        if effective_due == ZERO
        else "Pending"
    )

    return effective_due
