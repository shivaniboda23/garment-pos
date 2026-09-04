from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import String
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.models.customer import Customer
from app.models.product_variant import (
    ProductVariant,
)
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.shop import Shop
from app.models.stock import Stock

from app.services.stock_movement import (
    record_stock_movement,
)


# ==========================================================
# Generate Invoice
# ==========================================================

def generate_invoice():
    return (
        f"INV-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )


# ==========================================================
# Create Sale
# ==========================================================

def create_sale(
    db: Session,
    shop_id: int,
    data,
):
    try:

        # --------------------------------------------------
        # Validate Shop
        # --------------------------------------------------

        shop = (
            db.query(Shop)
            .filter(
                Shop.id
                == shop_id,
            )
            .first()
        )

        if not shop:
            raise HTTPException(
                status_code=404,
                detail="Shop not found.",
            )

        # --------------------------------------------------
        # Validate Customer
        # --------------------------------------------------

        if (
            data.customer_id
            is not None
        ):

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id
                    == data.customer_id,

                    Customer.shop_id
                    == shop_id,
                )
                .first()
            )

            if not customer:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found.",
                )

        # --------------------------------------------------
        # Validate Items
        # --------------------------------------------------

        if not data.items:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one sale "
                    "item is required."
                ),
            )

        variant_ids = [
            item.variant_id
            for item in data.items
        ]

        if len(variant_ids) != len(
            set(variant_ids)
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Duplicate variant in "
                    "sale items."
                ),
            )

        subtotal = (
            Decimal("0.00")
        )

        gst_total = (
            Decimal("0.00")
        )

        sale_items = []

        # --------------------------------------------------
        # Process Items
        # --------------------------------------------------

        for item in data.items:

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Quantity for "
                        f"variant "
                        f"{item.variant_id} "
                        f"must be greater "
                        f"than zero."
                    ),
                )

            if item.k_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "K quantity cannot "
                        "be negative."
                    ),
                )

            if item.r_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "R quantity cannot "
                        "be negative."
                    ),
                )

            if item.quantity != (
                item.k_quantity
                + item.r_quantity
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Total quantity must "
                        "equal K Quantity "
                        "+ R Quantity for "
                        f"variant "
                        f"{item.variant_id}."
                    ),
                )

            if item.discount < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Discount cannot "
                        "be negative."
                    ),
                )

            # ------------------------------------------------
            # Lock Variant
            # ------------------------------------------------

            variant_row = (
                db.query(
                    ProductVariant,
                    Product,
                )
                .join(
                    Product,
                    Product.id
                    == ProductVariant.product_id,
                )
                .filter(
                    ProductVariant.id
                    == item.variant_id,

                    Product.shop_id
                    == shop_id,
                )
                .with_for_update(
                    of=ProductVariant
                )
                .first()
            )

            if not variant_row:
                raise HTTPException(
                    status_code=404,
                    detail="Variant not found.",
                )

            variant, product = (
                variant_row
            )

            stock = (
                db.query(Stock)
                .filter(
                    Stock.variant_id
                    == variant.id,
                )
                .with_for_update(
                    of=Stock
                )
                .first()
            )

            if not stock:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Stock record not "
                        f"found for variant "
                        f"{variant.id}."
                    ),
                )

            # ------------------------------------------------
            # Validate Stock
            # ------------------------------------------------

            if (
                item.k_quantity
                > stock.k_stock
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Not enough K "
                        f"Stock for SKU "
                        f"{variant.sku}. "
                        f"Available: "
                        f"{stock.k_stock}, "
                        f"requested: "
                        f"{item.k_quantity}."
                    ),
                )

            if (
                item.r_quantity
                > stock.r_stock
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Not enough R "
                        f"Stock for SKU "
                        f"{variant.sku}. "
                        f"Available: "
                        f"{stock.r_stock}, "
                        f"requested: "
                        f"{item.r_quantity}."
                    ),
                )

            # ------------------------------------------------
            # Determine Stock Source
            # ------------------------------------------------

            if (
                item.k_quantity > 0
                and item.r_quantity > 0
            ):

                stock_type = (
                    "MIXED"
                )

            elif item.k_quantity > 0:

                stock_type = "K"

            else:

                stock_type = "R"

            # ------------------------------------------------
            # Pricing
            # ------------------------------------------------

            unit_price = Decimal(
                str(
                    variant.selling_price
                    or 0
                )
            )

            cost_price = Decimal(
                str(
                    variant.cost_price
                    or 0
                )
            )

            if cost_price <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cost price is not "
                        f"configured for SKU "
                        f"{variant.sku}. "
                        "Please set a valid "
                        "cost price before "
                        "selling this item."
                    ),
                )

            line_total = (
                unit_price
                * Decimal(
                    item.quantity
                )
            )

            line_total -= (
                Decimal(
                    str(
                        item.discount
                    )
                )
            )

            if line_total < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Discount cannot "
                        f"exceed line value "
                        f"for SKU "
                        f"{variant.sku}."
                    ),
                )

            gst_percentage = (
                Decimal(
                    str(
                        product
                        .gst_percentage
                        or 0
                    )
                )
            )

            gst = (
                line_total
                * gst_percentage
                / Decimal("100")
            )

            subtotal += (
                line_total
            )

            gst_total += (
                gst
            )

            sale_items.append(
                {
                    "variant":
                        variant,

                    "stock":
                        stock,

                    "quantity":
                        item.quantity,

                    "k_quantity":
                        item.k_quantity,

                    "r_quantity":
                        item.r_quantity,

                    "stock_type":
                        stock_type,

                    "cost_price":
                        cost_price,

                    "unit_price":
                        unit_price,

                    "discount":
                        Decimal(
                            str(
                                item.discount
                            )
                        ),

                    "gst":
                        gst,

                    "total":
                        line_total + gst,
                }
            )

        # --------------------------------------------------
        # Sale Discount
        # --------------------------------------------------

        sale_discount = Decimal(
            str(
                data.discount or 0
            )
        )

        if sale_discount < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Sale discount "
                    "cannot be negative."
                ),
            )

        if sale_discount > (
            subtotal + gst_total
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Sale discount cannot "
                    "exceed sale total."
                ),
            )

        grand_total = (
            subtotal
            + gst_total
            - sale_discount
        )

        # --------------------------------------------------
        # Generate Invoice
        # --------------------------------------------------

        invoice = (
            generate_invoice()
        )

        while (
            db.query(Sale)
            .filter(
                Sale.invoice_number
                == invoice,
            )
            .first()
        ):
            invoice = (
                generate_invoice()
            )

        # --------------------------------------------------
        # Create Sale
        # --------------------------------------------------

        sale = Sale(
            shop_id=shop_id,
            customer_id=
                data.customer_id,

            invoice_number=
                invoice,

            subtotal=
                subtotal,

            discount=
                sale_discount,

            gst_amount=
                gst_total,

            total_amount=
                grand_total,

            payment_method=
                data.payment_method,

            status=
                "Completed",
        )

        db.add(
            sale
        )

        db.flush()

        # --------------------------------------------------
        # Save Items + Deduct Stock
        # --------------------------------------------------

        for row in sale_items:

            variant = (
                row["variant"]
            )

            stock = (
                row["stock"]
            )

            # ==============================================
            # K STOCK MOVEMENT
            # ==============================================

            if row["k_quantity"] > 0:

                k_before = int(
                    stock.k_stock
                    or 0
                )

                stock.k_stock -= (
                    row["k_quantity"]
                )

                k_after = int(
                    stock.k_stock
                    or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=
                        shop_id,

                    variant_id=
                        variant.id,

                    movement_type=
                        "SALE",

                    stock_type=
                        "K",

                    quantity=(
                        -row[
                            "k_quantity"
                        ]
                    ),

                    quantity_before=
                        k_before,

                    quantity_after=
                        k_after,

                    reference_type=
                        "SALE",

                    reference_id=
                        sale.id,

                    reference_number=
                        sale.invoice_number,
                )

            # ==============================================
            # R STOCK MOVEMENT
            # ==============================================

            if row["r_quantity"] > 0:

                r_before = int(
                    stock.r_stock
                    or 0
                )

                stock.r_stock -= (
                    row["r_quantity"]
                )

                r_after = int(
                    stock.r_stock
                    or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=
                        shop_id,

                    variant_id=
                        variant.id,

                    movement_type=
                        "SALE",

                    stock_type=
                        "R",

                    quantity=(
                        -row[
                            "r_quantity"
                        ]
                    ),

                    quantity_before=
                        r_before,

                    quantity_after=
                        r_after,

                    reference_type=
                        "SALE",

                    reference_id=
                        sale.id,

                    reference_number=
                        sale.invoice_number,
                )

            # ------------------------------------------------
            # Save Sale Item
            # ------------------------------------------------

            sale_item = SaleItem(
                sale_id=
                    sale.id,

                variant_id=
                    variant.id,

                quantity=
                    row["quantity"],

                stock_type=
                    row["stock_type"],

                k_quantity=
                    row["k_quantity"],

                r_quantity=
                    row["r_quantity"],

                cost_price=
                    row["cost_price"],

                unit_price=
                    row["unit_price"],

                discount=
                    row["discount"],

                gst=
                    row["gst"],

                total_price=
                    row["total"],
            )

            db.add(
                sale_item
            )

        # --------------------------------------------------
        # Commit
        # --------------------------------------------------

        db.commit()

        db.refresh(
            sale
        )

        return sale

    except HTTPException:
        db.rollback()
        raise

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Sale creation "
                "could not be completed."
            ),
        )


# ==========================================================
# Sales History
# ==========================================================

def get_all_sales(
    db: Session,
    shop_id: int,
    invoice: str | None = None,
    customer_id: int | None = None,
    date: str | None = None,
):

    query = (
        db.query(Sale)
        .options(
            joinedload(
                Sale.customer
            ),

            joinedload(
                Sale.items
            )
            .joinedload(
                SaleItem.variant
            ),
        )
        .filter(
            Sale.shop_id
            == shop_id,
        )
    )

    if invoice:
        query = query.filter(
            Sale.invoice_number.ilike(
                f"%{invoice}%"
            )
        )

    if customer_id:
        query = query.filter(
            Sale.customer_id
            == customer_id
        )

    if date:
        query = query.filter(
            Sale.created_at
            .cast(String)
            .like(
                f"{date}%"
            )
        )

    return (
        query
        .order_by(
            Sale.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Sale Details
# ==========================================================

def get_sale_by_id(
    db: Session,
    sale_id: int,
    shop_id: int,
):

    return (
        db.query(Sale)
        .options(
            joinedload(
                Sale.customer
            ),

            joinedload(
                Sale.items
            )
            .joinedload(
                SaleItem.variant
            ),
        )
        .filter(
            Sale.id
            == sale_id,

            Sale.shop_id
            == shop_id,
        )
        .first()
    )
