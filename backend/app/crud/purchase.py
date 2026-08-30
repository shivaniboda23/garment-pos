from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.product_variant import ProductVariant
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

        # --------------------------------------------------
        # Basic Amount Validation
        # --------------------------------------------------

        grand_total = Decimal(
            str(
                data.grand_total or 0
            )
        )

        paid_amount = Decimal(
            str(
                data.paid_amount or 0
            )
        )

        balance_amount = Decimal(
            str(
                data.balance_amount or 0
            )
        )

        if grand_total < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Grand total cannot be negative."
                ),
            )

        if paid_amount < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Paid amount cannot be negative."
                ),
            )

        if balance_amount < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Balance amount cannot be negative."
                ),
            )

        calculated_balance = (
            grand_total
            - paid_amount
        )

        if calculated_balance < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Paid amount cannot exceed "
                    "grand total."
                ),
            )

        if round(
            calculated_balance,
            2,
        ) != round(
            balance_amount,
            2,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Balance amount must equal "
                    "Grand Total - Paid Amount."
                ),
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
        # Create Purchase
        # --------------------------------------------------

        purchase = Purchase(
            shop_id=shop_id,
            supplier_id=data.supplier_id,

            invoice_number=
                generate_purchase_number(
                    shop_id
                ),

            supplier_invoice=
                data.supplier_invoice,

            subtotal=data.subtotal,
            discount=data.discount,
            gst=data.gst,

            grand_total=grand_total,

            paid_amount=paid_amount,

            balance_amount=
                balance_amount,

            status=(
                "Completed"
                if balance_amount == 0
                else "Pending"
            ),
        )

        db.add(purchase)
        db.flush()

        # --------------------------------------------------
        # Process Purchase Items
        # --------------------------------------------------

        for item in data.items:

            variant = (
                db.query(ProductVariant)
                .options(
                    joinedload(
                        ProductVariant.product
                    ),

                    joinedload(
                        ProductVariant.stock
                    ),
                )
                .filter(
                    ProductVariant.id
                    == item.variant_id,
                )
                .with_for_update()
                .first()
            )

            if not variant:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Variant "
                        f"{item.variant_id} "
                        f"not found."
                    ),
                )

            if not variant.product:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Product for variant "
                        f"{variant.id} "
                        f"not found."
                    ),
                )

            if (
                variant.product.shop_id
                != shop_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Variant does not "
                        "belong to this shop."
                    ),
                )

            if not variant.stock:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Stock record "
                        f"missing for "
                        f"Variant "
                        f"{variant.id}."
                    ),
                )

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Purchase quantity "
                        "must be greater "
                        "than zero."
                    ),
                )

            if item.cost_price < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cost price cannot "
                        "be negative."
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

            # ==================================================
            # UPDATE STOCK + RECORD MOVEMENT
            # ==================================================

            if stock_type == "K":

                stock_before = int(
                    variant.stock.k_stock
                    or 0
                )

                variant.stock.k_stock += (
                    item.quantity
                )

                stock_after = int(
                    variant.stock.k_stock
                    or 0
                )

            else:

                stock_before = int(
                    variant.stock.r_stock
                    or 0
                )

                variant.stock.r_stock += (
                    item.quantity
                )

                stock_after = int(
                    variant.stock.r_stock
                    or 0
                )

            record_stock_movement(
                db=db,
                shop_id=shop_id,
                variant_id=variant.id,
                movement_type="PURCHASE",
                stock_type=stock_type,
                quantity=item.quantity,
                quantity_before=stock_before,
                quantity_after=stock_after,
                reference_type="PURCHASE",
                reference_id=purchase.id,
                reference_number=(
                    purchase.invoice_number
                ),
                reason=None,
                notes=None,
            )

            # --------------------------------------------------
            # Save Purchase Item
            # --------------------------------------------------

            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                stock_type=stock_type,
                cost_price=item.cost_price,
                gst_percentage=item.gst_percentage,
                discount=item.discount,
                total=item.total,
            )

            db.add(
                purchase_item
            )

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

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Purchase creation failed: "
                f"{str(exc)}"
            ),
        )


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