from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.payment import Payment
from app.models.sale import Sale
from app.models.sale_return import SaleReturn


ZERO = Decimal("0.00")


def _decimal(value) -> Decimal:
    if value is None:
        raise ValueError("Invalid customer receivable value.")

    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            "Invalid customer receivable value."
        ) from exc

    if not result.is_finite():
        raise ValueError("Invalid customer receivable value.")

    return result


def _payment_status(
    payments: Decimal,
    effective_obligation: Decimal,
) -> str:
    if (
        effective_obligation == ZERO
        or payments >= effective_obligation
    ):
        return "Paid"

    if payments > ZERO:
        return "Partial"

    return "Pending"


@dataclass(frozen=True)
class BillReceivable:
    original_total: Decimal
    payments: Decimal
    completed_returns: Decimal
    effective_obligation: Decimal
    due: Decimal
    refundable_entitlement: Decimal
    payment_status: str


def calculate_bill_receivable(
    original_total,
    payments,
    completed_returns,
) -> BillReceivable:
    original_total = _decimal(original_total)
    payments = _decimal(payments)
    completed_returns = _decimal(completed_returns)

    if (
        original_total < ZERO
        or payments < ZERO
        or completed_returns < ZERO
    ):
        raise ValueError("Invalid customer receivable history.")

    effective_obligation = max(
        original_total - completed_returns,
        ZERO,
    )
    due = max(
        effective_obligation - payments,
        ZERO,
    )
    refundable_entitlement = max(
        payments - effective_obligation,
        ZERO,
    )

    return BillReceivable(
        original_total=original_total,
        payments=payments,
        completed_returns=completed_returns,
        effective_obligation=effective_obligation,
        due=due,
        refundable_entitlement=refundable_entitlement,
        payment_status=_payment_status(
            payments=payments,
            effective_obligation=effective_obligation,
        ),
    )


def get_bill_receivable(
    db: Session,
    shop_id: int,
    bill: Bill,
) -> BillReceivable:
    if bill.shop_id != shop_id:
        raise ValueError("Invalid Bill relationship.")

    payments = (
        db.query(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        )
        .filter(Payment.bill_id == bill.id)
        .scalar()
    )

    completed_returns = ZERO

    if bill.sale_id is not None:
        sale = (
            db.query(Sale)
            .filter(Sale.id == bill.sale_id)
            .first()
        )

        if (
            sale is None
            or sale.shop_id != shop_id
            or sale.customer_id != bill.customer_id
        ):
            raise ValueError("Invalid Bill/Sale relationship.")

        completed_returns = (
            db.query(
                func.coalesce(
                    func.sum(SaleReturn.refund_amount),
                    0,
                )
            )
            .filter(
                SaleReturn.shop_id == shop_id,
                SaleReturn.sale_id == bill.sale_id,
                SaleReturn.status == "Completed",
            )
            .scalar()
        )

    return calculate_bill_receivable(
        original_total=bill.grand_total,
        payments=payments,
        completed_returns=completed_returns,
    )


def sync_bill_payment_status(
    db: Session,
    shop_id: int,
    bill: Bill,
) -> BillReceivable:
    state = get_bill_receivable(
        db=db,
        shop_id=shop_id,
        bill=bill,
    )
    bill.payment_status = state.payment_status
    return state
