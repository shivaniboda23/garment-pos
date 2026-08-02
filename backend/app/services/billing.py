from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Any

MONEY_QUANTIZER = Decimal("0.01")


# ==========================================================
# MONEY HELPERS
# ==========================================================

def to_money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")

    if isinstance(value, Decimal):
        return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    return Decimal(str(value)).quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


# ==========================================================
# INVOICE NUMBER
# ==========================================================

def generate_invoice_number(shop_id: int) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    return f"INV-{shop_id}-{timestamp}"


# ==========================================================
# LINE CALCULATION
# ==========================================================

def calculate_line_totals(
    selling_price: Any,
    ordered_qty: int,
    discount: Any,
    gst_percentage: Any,
) -> dict[str, Decimal]:
    unit_price = to_money(selling_price)
    discount_amount = to_money(discount)
    gst_rate = to_money(gst_percentage)

    gross_amount = to_money(unit_price * Decimal(ordered_qty))
    taxable_amount = gross_amount - discount_amount

    if taxable_amount < 0:
        taxable_amount = Decimal("0.00")

    gst_amount = to_money(
        taxable_amount
        * gst_rate
        / Decimal("100")
    )

    total = to_money(taxable_amount + gst_amount)

    return {
        "unit_price": unit_price,
        "gross_amount": gross_amount,
        "taxable_amount": taxable_amount,
        "discount_amount": discount_amount,
        "gst_rate": gst_rate,
        "gst_amount": gst_amount,
        "total": total,
    }


# ==========================================================
# STATUS HELPERS
# ==========================================================

def resolve_payment_method(payments: Iterable[Any] | None) -> str:
    methods: list[str] = []

    for payment in payments or []:
        method = str(
            getattr(
                payment,
                "payment_mode",
                "",
            ) or ""
        ).strip()

        if method and method not in methods:
            methods.append(method)

    if not methods:
        return "Cash"

    if len(methods) == 1:
        return methods[0]

    return "Multiple"


def resolve_payment_status(
    total_paid: Any,
    grand_total: Any,
) -> str:
    paid = to_money(total_paid)
    total = to_money(grand_total)

    if paid >= total:
        return "Paid"

    if paid > 0:
        return "Partial"

    return "Pending"


def resolve_bill_status(
    has_pending_items: bool,
) -> str:
    if has_pending_items:
        return "Partial Delivery"

    return "Completed"
