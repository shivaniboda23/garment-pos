from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.stock import Stock
from app.models.supplier_payment import SupplierPayment

from app.services.stock_movement import (
    record_stock_movement,
)


# ==========================================================
# Generate Purchase Number
# ==========================================================

def generate_purchase_number(
    shop_id: int,
):
    now = datetime.now()

    return (
        f"PUR-{shop_id}-"
        f"{now.strftime('%Y%m%d%H%M%S%f')[:-3]}"
    )


# ==========================================================
# Create Purchase
# ==========================================================

def create_purchase(
    db: Session,
    shop_id: int,
    data,
):
    try:
        money_unit = Decimal("0.01")

        def to_money(value) -> Decimal:
            return Decimal(
                str(value or 0)
            ).quantize(
                money_unit,
                rounding=ROUND_HALF_UP,
            )

        # --------------------------------------------------
        # Validate Supplier
        # --------------------------------------------------

        from app.models.supplier import Supplier

        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id
                == data.supplier_id,

                Supplier.shop_id
                == shop_id,

                Supplier.is_active
                == True,
            )
            .first()
        )

        if not supplier:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found.",
            )

        # --------------------------------------------------
        # Validate Items
        # --------------------------------------------------

        if not data.items:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one purchase "
                    "item is required."
                ),
            )

        # --------------------------------------------------
        # Prepare and Validate Items
        # --------------------------------------------------

        prepared_items = []
        item_keys = set()

        for item in data.items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Purchase quantity "
                        "must be greater "
                        "than zero."
                    ),
                )

            stock_type = (
                str(
                    item.stock_type
                )
                .strip()
                .upper()
            )

            if stock_type not in (
                "K",
                "R",
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid stock type."
                    ),
                )

            item_key = (
                item.variant_id,
                stock_type,
            )

            if item_key in item_keys:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Duplicate variant and stock type "
                        "in purchase items."
                    ),
                )

            item_keys.add(item_key)

            raw_cost_price = Decimal(
                str(item.cost_price or 0)
            )
            raw_discount = Decimal(
                str(item.discount or 0)
            )
            raw_gst_percentage = Decimal(
                str(item.gst_percentage or 0)
            )

            if raw_cost_price < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cost price cannot be negative.",
                )

            if raw_discount < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Line discount cannot be negative.",
                )

            if raw_gst_percentage < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "GST percentage cannot be negative."
                    ),
                )

            cost_price = to_money(raw_cost_price)
            discount = to_money(raw_discount)
            gst_percentage = to_money(
                raw_gst_percentage
            )
            line_total = max(
                (
                    Decimal(item.quantity)
                    * cost_price
                    - discount
                ).quantize(
                    money_unit,
                    rounding=ROUND_HALF_UP,
                ),
                Decimal("0.00"),
            )

            prepared_items.append({
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "stock_type": stock_type,
                "cost_price": cost_price,
                "gst_percentage": gst_percentage,
                "discount": discount,
                "total": line_total,
            })

        prepared_items.sort(
            key=lambda item: (
                item["variant_id"],
                item["stock_type"],
            )
        )

        # --------------------------------------------------
        # Calculate Authoritative Header Amounts
        # --------------------------------------------------

        subtotal = sum(
            (
                item["total"]
                for item in prepared_items
            ),
            Decimal("0.00"),
        ).quantize(
            money_unit,
            rounding=ROUND_HALF_UP,
        )
        raw_header_discount = Decimal(
            str(data.discount or 0)
        )
        raw_header_gst = Decimal(
            str(data.gst or 0)
        )
        raw_paid_amount = Decimal(
            str(data.paid_amount or 0)
        )

        if raw_header_discount < 0:
            raise HTTPException(
                status_code=400,
                detail="Discount cannot be negative.",
            )

        if raw_header_gst < 0:
            raise HTTPException(
                status_code=400,
                detail="GST cannot be negative.",
            )

        if raw_paid_amount < 0:
            raise HTTPException(
                status_code=400,
                detail="Paid amount cannot be negative.",
            )

        header_discount = to_money(
            raw_header_discount
        )
        header_gst = to_money(raw_header_gst)
        paid_amount = to_money(raw_paid_amount)
        grand_total = max(
            subtotal - header_discount + header_gst,
            Decimal("0.00"),
        ).quantize(
            money_unit,
            rounding=ROUND_HALF_UP,
        )

        if paid_amount > grand_total:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Paid amount cannot exceed "
                    "grand total."
                ),
            )

        balance_amount = (
            grand_total - paid_amount
        ).quantize(
            money_unit,
            rounding=ROUND_HALF_UP,
        )

        # --------------------------------------------------
        # Lock Variants and Stocks Deterministically
        # --------------------------------------------------

        unique_variant_ids = sorted({
            item["variant_id"]
            for item in prepared_items
        })
        variants = (
            db.query(ProductVariant)
            .join(
                Product,
                Product.id
                == ProductVariant.product_id,
            )
            .filter(
                ProductVariant.id.in_(
                    unique_variant_ids
                ),
                Product.shop_id == shop_id,
            )
            .order_by(ProductVariant.id.asc())
            .with_for_update(of=ProductVariant)
            .all()
        )
        variants_by_id = {
            variant.id: variant
            for variant in variants
        }

        if len(variants_by_id) != len(
            unique_variant_ids
        ):
            raise HTTPException(
                status_code=404,
                detail="Variant not found.",
            )

        stocks = (
            db.query(Stock)
            .filter(
                Stock.variant_id.in_(
                    unique_variant_ids
                )
            )
            .order_by(Stock.variant_id.asc())
            .with_for_update(of=Stock)
            .all()
        )
        stocks_by_variant = {
            stock.variant_id: stock
            for stock in stocks
        }

        if len(stocks_by_variant) != len(
            unique_variant_ids
        ):
            raise HTTPException(
                status_code=500,
                detail="Stock record missing for variant.",
            )

        # --------------------------------------------------
        # Create Purchase Header
        # --------------------------------------------------

        purchase = Purchase(
            shop_id=shop_id,
            supplier_id=data.supplier_id,
            invoice_number=generate_purchase_number(
                shop_id
            ),
            supplier_invoice=data.supplier_invoice,
            subtotal=subtotal,
            discount=header_discount,
            gst=header_gst,
            grand_total=grand_total,
            paid_amount=paid_amount,
            balance_amount=balance_amount,
            status=(
                "Completed"
                if balance_amount == 0
                else "Pending"
            ),
        )

        db.add(purchase)
        db.flush()

        # --------------------------------------------------
        # Apply Stock and Create Purchase Items
        # --------------------------------------------------

        for item in prepared_items:
            variant = variants_by_id[
                item["variant_id"]
            ]
            stock = stocks_by_variant[
                item["variant_id"]
            ]

            if item["stock_type"] == "K":
                stock_before = int(
                    stock.k_stock or 0
                )
                stock.k_stock = (
                    stock_before
                    + item["quantity"]
                )
                stock_after = int(
                    stock.k_stock or 0
                )
            else:
                stock_before = int(
                    stock.r_stock or 0
                )
                stock.r_stock = (
                    stock_before
                    + item["quantity"]
                )
                stock_after = int(
                    stock.r_stock or 0
                )

            record_stock_movement(
                db=db,
                shop_id=shop_id,
                variant_id=variant.id,
                movement_type="PURCHASE",
                stock_type=item["stock_type"],
                quantity=item["quantity"],
                quantity_before=stock_before,
                quantity_after=stock_after,
                reference_type="PURCHASE",
                reference_id=purchase.id,
                reference_number=purchase.invoice_number,
                reason=None,
                notes=None,
            )

            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                variant_id=item["variant_id"],
                quantity=item["quantity"],
                stock_type=item["stock_type"],
                cost_price=item["cost_price"],
                gst_percentage=item["gst_percentage"],
                discount=item["discount"],
                total=item["total"],
            )

            db.add(purchase_item)

        # --------------------------------------------------
        # Create Initial Supplier Payment
        # --------------------------------------------------

        if paid_amount > 0:

            payment_method = getattr(
                data,
                "payment_method",
                "Cash",
            )

            initial_payment = (
                SupplierPayment(
                    shop_id=shop_id,
                    supplier_id=
                        data.supplier_id,
                    purchase_id=
                        purchase.id,
                    amount=
                        paid_amount,
                    payment_method=
                        payment_method,
                    reference_number=(
                        getattr(
                            data,
                            "payment_reference",
                            None,
                        )
                    ),
                    notes=(
                        "Initial payment at "
                        "purchase creation."
                    ),
                )
            )

            db.add(
                initial_payment
            )

        # --------------------------------------------------
        # Commit Everything
        # --------------------------------------------------

        db.commit()

        db.refresh(
            purchase
        )

        return purchase

    except HTTPException:
        db.rollback()
        raise

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Purchase creation could not "
                "be completed."
            ),
        ) from None


# ==========================================================
# Purchase History
# ==========================================================

def get_all_purchases(
    db: Session,
    shop_id: int,
    invoice: str | None = None,
    supplier_id: int | None = None,
    status: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):

    query = (
        db.query(Purchase)
        .options(
            joinedload(
                Purchase.supplier
            )
        )
        .filter(
            Purchase.shop_id
            == shop_id
        )
    )

    if invoice:
        query = query.filter(
            Purchase.invoice_number.ilike(
                f"%{invoice}%"
            )
        )

    if supplier_id:
        query = query.filter(
            Purchase.supplier_id
            == supplier_id
        )

    if status:
        query = query.filter(
            Purchase.status
            == status
        )

    if from_date:
        query = query.filter(
            Purchase.created_at
            >= from_date
        )

    if to_date:
        query = query.filter(
            Purchase.created_at
            <= to_date
        )

    return (
        query
        .order_by(
            Purchase.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Purchase Details
# ==========================================================

def get_purchase_by_id(
    db: Session,
    purchase_id: int,
    shop_id: int,
):

    return (
        db.query(Purchase)
        .options(
            joinedload(
                Purchase.supplier
            ),

            joinedload(
                Purchase.items
            )
            .joinedload(
                PurchaseItem.variant
            ),

            joinedload(
                Purchase.payments
            ),
        )
        .filter(
            Purchase.id
            == purchase_id,

            Purchase.shop_id
            == shop_id,
        )
        .first()
    )


# ==========================================================
# Search Purchase By Invoice
# ==========================================================

def search_purchase_invoice(
    db: Session,
    shop_id: int,
    invoice: str,
):

    return (
        db.query(Purchase)
        .filter(
            Purchase.shop_id
            == shop_id,

            Purchase.invoice_number.ilike(
                f"%{invoice}%"
            ),
        )
        .all()
    )


# ==========================================================
# Search Purchase By Supplier
# ==========================================================

def search_purchase_supplier(
    db: Session,
    shop_id: int,
    supplier_id: int,
):

    return (
        db.query(Purchase)
        .filter(
            Purchase.shop_id
            == shop_id,

            Purchase.supplier_id
            == supplier_id,
        )
        .order_by(
            Purchase.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Pending Purchases
# ==========================================================

def get_pending_purchases(
    db: Session,
    shop_id: int,
):

    return (
        db.query(Purchase)
        .filter(
            Purchase.shop_id
            == shop_id,

            Purchase.status
            == "Pending",
        )
        .order_by(
            Purchase.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Completed Purchases
# ==========================================================

def get_completed_purchases(
    db: Session,
    shop_id: int,
):

    return (
        db.query(Purchase)
        .filter(
            Purchase.shop_id
            == shop_id,

            Purchase.status
            == "Completed",
        )
        .order_by(
            Purchase.created_at.desc()
        )
        .all()
    )
