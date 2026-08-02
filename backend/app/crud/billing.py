from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.product_variant import ProductVariant

from app.services.billing import (
    calculate_line_totals,
    generate_invoice_number,
    resolve_bill_status,
    resolve_payment_method,
    resolve_payment_status,
    to_money,
)


# ==========================================================
# CREATE BILL
# ==========================================================

def create_bill(
    db: Session,
    shop_id: int,
    data,
):
    if not data.items:
        raise ValueError("At least one bill item is required.")

    if data.customer_id is not None:
        customer = (
            db.query(Customer)
            .filter(
                Customer.id == data.customer_id,
                Customer.shop_id == shop_id,
                Customer.is_active == True,
            )
            .first()
        )

        if not customer:
            return None

    try:
        invoice_number = generate_invoice_number(shop_id)

        while (
            db.query(Bill)
            .filter(
                Bill.invoice_number == invoice_number,
            )
            .first()
        ):
            invoice_number = generate_invoice_number(shop_id)

        bill = Bill(
            shop_id=shop_id,
            customer_id=data.customer_id,
            invoice_number=invoice_number,
            subtotal=to_money(0),
            discount=to_money(data.discount),
            gst=to_money(0),
            grand_total=to_money(0),
            payment_method=resolve_payment_method(data.payments),
            payment_status="Pending",
            bill_status="Completed",
            remarks=getattr(data, "remarks", None),
        )

        db.add(bill)
        db.flush()

        subtotal = to_money(0)
        gst_total = to_money(0)
        has_pending_items = False

        for item in data.items:
            variant = (
                db.query(ProductVariant)
                .options(
                    joinedload(ProductVariant.product),
                    joinedload(ProductVariant.stock),
                )
                .filter(
                    ProductVariant.id == item.variant_id,
                )
                .first()
            )

            if not variant or not variant.product:
                raise ValueError(
                    f"Variant {item.variant_id} not found."
                )

            if variant.product.shop_id != shop_id:
                raise ValueError(
                    f"Variant {variant.id} does not belong to this shop."
                )

            if not variant.stock:
                raise ValueError(
                    f"Stock not found for variant {variant.id}."
                )

            if item.ordered_qty <= 0:
                raise ValueError(
                    "Ordered quantity must be greater than zero."
                )

            if item.k_quantity < 0:
                raise ValueError(
                    "K quantity cannot be negative."
                )

            if item.r_quantity < 0:
                raise ValueError(
                    "R quantity cannot be negative."
                )

            if item.ordered_qty != (item.k_quantity + item.r_quantity):
                raise ValueError(
                    f"Ordered quantity mismatch for SKU {variant.sku}."
                )

            stock = variant.stock

            if item.k_quantity > stock.k_stock:
                raise ValueError(
                    f"Only {stock.k_stock} K stock available for SKU {variant.sku}."
                )

            if item.r_quantity > stock.r_stock:
                raise ValueError(
                    f"Only {stock.r_stock} R stock available for SKU {variant.sku}."
                )

            totals = calculate_line_totals(
                selling_price=item.selling_price,
                ordered_qty=item.ordered_qty,
                discount=item.discount,
                gst_percentage=item.gst_percentage,
            )

            subtotal += totals["taxable_amount"]
            gst_total += totals["gst_amount"]

            stock.k_stock -= item.k_quantity
            stock.r_stock -= item.r_quantity

            delivered_qty = item.ordered_qty
            pending_qty = 0

            if pending_qty > 0:
                has_pending_items = True
                item_status = "Pending"
            else:
                item_status = "Delivered"

            bill_item = BillItem(
                bill_id=bill.id,
                variant_id=variant.id,
                ordered_qty=item.ordered_qty,
                delivered_qty=delivered_qty,
                pending_qty=pending_qty,
                k_delivered_qty=item.k_quantity,
                r_delivered_qty=item.r_quantity,
                k_quantity=item.k_quantity,
                r_quantity=item.r_quantity,
                selling_price=totals["unit_price"],
                discount=totals["discount_amount"],
                gst_percentage=totals["gst_rate"],
                gst=totals["gst_amount"],
                total=totals["total"],
                item_status=item_status,
            )

            db.add(bill_item)

        bill.subtotal = subtotal
        bill.discount = to_money(data.discount)
        bill.gst = gst_total
        bill.grand_total = to_money(
            subtotal + gst_total - bill.discount
        )
        bill.payment_method = resolve_payment_method(data.payments)
        bill.bill_status = resolve_bill_status(has_pending_items)

        total_paid = to_money(0)

        for pay in data.payments:
            amount = to_money(pay.amount)

            if amount < 0:
                raise ValueError("Payment amount cannot be negative.")

            total_paid += amount

            payment = Payment(
                bill_id=bill.id,
                amount=amount,
                payment_method=pay.payment_mode,
            )

            db.add(payment)

        bill.payment_status = resolve_payment_status(
            total_paid=total_paid,
            grand_total=bill.grand_total,
        )

        db.commit()

        return get_bill_by_id(
            db=db,
            bill_id=bill.id,
            shop_id=shop_id,
        )

    except Exception:
        db.rollback()
        raise


# ==========================================================
# BILL HISTORY
# ==========================================================

def get_all_bills(
    db: Session,
    shop_id: int,
):
    bills = (
        db.query(Bill)
        .options(
            joinedload(Bill.customer),
            joinedload(Bill.items)
            .joinedload(BillItem.variant),
            joinedload(Bill.payments),
        )
        .filter(
            Bill.shop_id == shop_id,
        )
        .order_by(
            Bill.created_at.desc(),
        )
        .all()
    )

    return bills


# ==========================================================
# BILL DETAILS
# ==========================================================

def get_bill_by_id(
    db: Session,
    bill_id: int,
    shop_id: int,
):
    bill = (
        db.query(Bill)
        .options(
            joinedload(Bill.customer),
            joinedload(Bill.items)
            .joinedload(BillItem.variant),
            joinedload(Bill.payments),
        )
        .filter(
            Bill.id == bill_id,
            Bill.shop_id == shop_id,
        )
        .first()
    )

    return bill


# ==========================================================
# SEARCH BILL
# ==========================================================

def search_bill(db: Session, shop_id: int, keyword: str):
    bills = (
        db.query(Bill)
        .options(
            joinedload(Bill.customer),
            joinedload(Bill.items).joinedload(BillItem.variant),
            joinedload(Bill.payments),
        )
        .outerjoin(Customer)
        .filter(Bill.shop_id == shop_id)
        .filter(
            or_(
                Bill.invoice_number.ilike(f"%{keyword}%"),
                Customer.customer_name.ilike(f"%{keyword}%"),
            )
        )
        .order_by(Bill.created_at.desc())
        .all()
    )
    return bills