from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.product_variant import (
    ProductVariant,
)
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock import Stock

from app.services.billing import (
    calculate_line_totals,
    generate_invoice_number,
    resolve_bill_status,
    resolve_payment_method,
    resolve_payment_status,
    to_money,
)

from app.services.stock_movement import (
    record_stock_movement,
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
        raise ValueError(
            "At least one bill item "
            "is required."
        )

    variant_ids = [
        item.variant_id
        for item in data.items
    ]

    if len(variant_ids) != len(
        set(variant_ids)
    ):
        raise ValueError(
            "Duplicate variant in bill items."
        )

    # ======================================================
    # CUSTOMER
    # ======================================================

    customer = None

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

                Customer.is_active
                .is_(True),
            )
            .first()
        )

        if not customer:
            return None

    try:

        # ==================================================
        # INVOICE
        # ==================================================

        invoice_number = (
            generate_invoice_number(
                shop_id
            )
        )

        while (
            db.query(Bill)
            .filter(
                Bill.invoice_number
                == invoice_number
            )
            .first()
        ) or (
            db.query(Sale)
            .filter(
                Sale.invoice_number
                == invoice_number
            )
            .first()
        ):

            invoice_number = (
                generate_invoice_number(
                    shop_id
                )
            )

        subtotal = to_money(0)
        gst_total = to_money(0)

        sale_item_data = []
        bill_item_data = []

        has_pending_items = False

        # ==================================================
        # PROCESS ITEMS
        # ==================================================

        for item in data.items:

            # ------------------------------------------------
            # VARIANT
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
                raise ValueError(
                    "Variant not found."
                )

            variant, product = (
                variant_row
            )

            # ------------------------------------------------
            # LOCK STOCK
            # ------------------------------------------------

            stock = (
                db.query(Stock)
                .filter(
                    Stock.variant_id
                    == variant.id
                )
                .with_for_update(
                    of=Stock
                )
                .first()
            )

            if not stock:
                raise ValueError(
                    f"Stock not found "
                    f"for variant "
                    f"{variant.id}."
                )

            # =================================================
            # QUANTITIES
            # =================================================

            ordered_qty = int(
                item.ordered_qty
                or 0
            )

            k_delivered_qty = int(
                item.k_quantity
                or 0
            )

            r_delivered_qty = int(
                item.r_quantity
                or 0
            )

            pending_k_qty = int(
                getattr(
                    item,
                    "pending_k_quantity",
                    0,
                )
                or 0
            )

            pending_r_qty = int(
                getattr(
                    item,
                    "pending_r_quantity",
                    0,
                )
                or 0
            )

            if ordered_qty <= 0:
                raise ValueError(
                    "Ordered quantity "
                    "must be greater "
                    "than zero."
                )

            quantities = [
                k_delivered_qty,
                r_delivered_qty,
                pending_k_qty,
                pending_r_qty,
            ]

            if any(
                qty < 0
                for qty
                in quantities
            ):
                raise ValueError(
                    "Item quantities "
                    "cannot be negative."
                )

            delivered_qty = (
                k_delivered_qty
                + r_delivered_qty
            )

            pending_qty = (
                pending_k_qty
                + pending_r_qty
            )

            if (
                ordered_qty
                != (
                    delivered_qty
                    + pending_qty
                )
            ):
                raise ValueError(
                    f"Quantity mismatch "
                    f"for SKU "
                    f"{variant.sku}."
                )

            # ------------------------------------------------
            # Customer is mandatory when something is pending.
            # ------------------------------------------------

            if (
                pending_qty > 0
                and data.customer_id
                is None
            ):
                raise ValueError(
                    f"Customer is required "
                    f"because SKU "
                    f"{variant.sku} "
                    f"has pending quantity."
                )

            if pending_qty > 0:
                has_pending_items = True

            # =================================================
            # STOCK CHECK
            #
            # Only delivered stock is checked.
            # Pending pieces do not exist in available stock yet.
            # =================================================

            current_k = int(
                stock.k_stock
                or 0
            )

            current_r = int(
                stock.r_stock
                or 0
            )

            if (
                k_delivered_qty
                > current_k
            ):
                raise ValueError(
                    f"Only "
                    f"{current_k} "
                    f"K stock available "
                    f"for SKU "
                    f"{variant.sku}."
                )

            if (
                r_delivered_qty
                > current_r
            ):
                raise ValueError(
                    f"Only "
                    f"{current_r} "
                    f"R stock available "
                    f"for SKU "
                    f"{variant.sku}."
                )

            # =================================================
            # COST PRICE
            # =================================================

            cost_price = Decimal(
                str(
                    variant.cost_price
                    or 0
                )
            )

            if cost_price <= 0:
                raise ValueError(
                    f"Cost price is not "
                    f"configured for "
                    f"SKU "
                    f"{variant.sku}. "
                    f"Please set a valid "
                    f"cost price first."
                )

            # =================================================
            # SELLING PRICE
            # =================================================

            variant_selling_price = (
                Decimal(
                    str(
                        variant
                        .selling_price
                        or 0
                    )
                )
            )

            if (
                variant_selling_price
                <= 0
            ):
                raise ValueError(
                    f"Selling price "
                    f"is not configured "
                    f"for SKU "
                    f"{variant.sku}."
                )

            # =================================================
            # BILL TOTAL
            #
            # Customer is billed for the entire ordered qty.
            # =================================================

            totals = (
                calculate_line_totals(
                    selling_price=
                        variant_selling_price,

                    ordered_qty=
                        ordered_qty,

                    discount=
                        item.discount,

                    gst_percentage=
                        product.gst_percentage,
                )
            )

            subtotal += (
                totals[
                    "taxable_amount"
                ]
            )

            gst_total += (
                totals[
                    "gst_amount"
                ]
            )

            # =================================================
            # TOTAL K/R ORDERED
            #
            # These go into BillItem.
            # =================================================

            total_k_ordered = (
                k_delivered_qty
                + pending_k_qty
            )

            total_r_ordered = (
                r_delivered_qty
                + pending_r_qty
            )

            # =================================================
            # STOCK TYPE
            #
            # For fully pending items use the ordered K/R split
            # instead of inventing another stock type.
            # =================================================

            reference_k = (
                k_delivered_qty
                if delivered_qty > 0
                else total_k_ordered
            )

            reference_r = (
                r_delivered_qty
                if delivered_qty > 0
                else total_r_ordered
            )

            if (
                reference_k > 0
                and reference_r > 0
            ):
                stock_type = (
                    "MIXED"
                )

            elif reference_k > 0:
                stock_type = "K"

            elif reference_r > 0:
                stock_type = "R"

            else:
                raise ValueError(
                    f"Invalid quantity "
                    f"for SKU "
                    f"{variant.sku}."
                )

            # =================================================
            # STATUS
            # =================================================

            if pending_qty == 0:
                item_status = (
                    "Delivered"
                )

            elif delivered_qty == 0:
                item_status = (
                    "Pending"
                )

            else:
                item_status = (
                    "Partially Delivered"
                )

            # =================================================
            # SALE ITEM
            #
            # IMPORTANT:
            #
            # quantity = delivered quantity.
            #
            # This ensures COGS reflects only units actually
            # fulfilled so far.
            #
            # total_price still represents the full billed line.
            # =================================================

            sale_item_data.append(
                {
                    "variant":
                        variant,

                    "stock":
                        stock,

                    "variant_id":
                        variant.id,

                    "quantity":
                        delivered_qty,

                    "stock_type":
                        stock_type,

                    "k_quantity":
                        k_delivered_qty,

                    "r_quantity":
                        r_delivered_qty,

                    "cost_price":
                        cost_price,

                    "unit_price":
                        totals[
                            "unit_price"
                        ],

                    "discount":
                        totals[
                            "discount_amount"
                        ],

                    "gst":
                        totals[
                            "gst_amount"
                        ],

                    "total_price":
                        totals[
                            "total"
                        ],
                }
            )

            # =================================================
            # BILL ITEM
            #
            # k_quantity / r_quantity =
            # TOTAL ORDERED K/R.
            #
            # k_delivered_qty / r_delivered_qty =
            # quantity already given to customer.
            # =================================================

            bill_item_data.append(
                {
                    "variant_id":
                        variant.id,

                    "ordered_qty":
                        ordered_qty,

                    "delivered_qty":
                        delivered_qty,

                    "pending_qty":
                        pending_qty,

                    "k_quantity":
                        total_k_ordered,

                    "r_quantity":
                        total_r_ordered,

                    "k_delivered_qty":
                        k_delivered_qty,

                    "r_delivered_qty":
                        r_delivered_qty,

                    "selling_price":
                        totals[
                            "unit_price"
                        ],

                    "discount":
                        totals[
                            "discount_amount"
                        ],

                    "gst_percentage":
                        totals[
                            "gst_rate"
                        ],

                    "gst":
                        totals[
                            "gst_amount"
                        ],

                    "total":
                        totals[
                            "total"
                        ],

                    "item_status":
                        item_status,
                }
            )

        # ==================================================
        # SALE DISCOUNT
        # ==================================================

        sale_discount = to_money(
            data.discount
        )

        if sale_discount < 0:
            raise ValueError(
                "Discount cannot "
                "be negative."
            )

        gross_before_discount = (
            subtotal
            + gst_total
        )

        if (
            sale_discount
            > gross_before_discount
        ):
            raise ValueError(
                "Discount cannot "
                "exceed bill total."
            )

        grand_total = to_money(
            gross_before_discount
            - sale_discount
        )

        if grand_total < 0:
            raise ValueError(
                "Bill total cannot "
                "be negative."
            )

        # ==================================================
        # PAYMENT VALIDATION
        # ==================================================

        total_paid = to_money(
            0
        )

        for payment_data in (
            data.payments
        ):

            amount = to_money(
                payment_data.amount
            )

            if amount < 0:
                raise ValueError(
                    "Payment amount "
                    "cannot be negative."
                )

            total_paid += amount

        if (
            total_paid
            > grand_total
        ):
            raise ValueError(
                "Total payment "
                "cannot exceed "
                "bill total."
            )

        # --------------------------------------------------
        # Due bill requires customer.
        # --------------------------------------------------

        if (
            total_paid
            < grand_total
            and data.customer_id
            is None
        ):
            raise ValueError(
                "Customer is required "
                "for a partial or "
                "unpaid bill."
            )

        # ==================================================
        # CREATE SALE
        # ==================================================

        payment_method = (
            resolve_payment_method(
                data.payments
            )
        )

        sale = Sale(
            shop_id=
                shop_id,

            customer_id=
                data.customer_id,

            invoice_number=
                invoice_number,

            subtotal=
                subtotal,

            discount=
                sale_discount,

            gst_amount=
                gst_total,

            total_amount=
                grand_total,

            payment_method=
                payment_method,

            # Financial sale is created now.
            status=
                "Completed",
        )

        db.add(
            sale
        )

        db.flush()

        # ==================================================
        # SALE ITEMS + STOCK + STOCK MOVEMENTS
        # ==================================================

        for row in (
            sale_item_data
        ):

            variant = (
                row["variant"]
            )

            stock = (
                row["stock"]
            )

            # ------------------------------------------------
            # FINAL K CHECK
            # ------------------------------------------------

            if (
                int(
                    stock.k_stock
                    or 0
                )
                < row[
                    "k_quantity"
                ]
            ):
                raise ValueError(
                    f"Insufficient "
                    f"K stock for "
                    f"SKU "
                    f"{variant.sku}."
                )

            # ------------------------------------------------
            # FINAL R CHECK
            # ------------------------------------------------

            if (
                int(
                    stock.r_stock
                    or 0
                )
                < row[
                    "r_quantity"
                ]
            ):
                raise ValueError(
                    f"Insufficient "
                    f"R stock for "
                    f"SKU "
                    f"{variant.sku}."
                )

            # =================================================
            # K STOCK MOVEMENT
            # =================================================

            if (
                row[
                    "k_quantity"
                ]
                > 0
            ):

                before = int(
                    stock.k_stock
                    or 0
                )

                stock.k_stock = (
                    before
                    - row[
                        "k_quantity"
                    ]
                )

                after = int(
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
                        before,

                    quantity_after=
                        after,

                    reference_type=
                        "SALE",

                    reference_id=
                        sale.id,

                    reference_number=
                        sale.invoice_number,

                    reason=
                        None,

                    notes=(
                        "Stock delivered "
                        "through billing."
                    ),
                )

            # =================================================
            # R STOCK MOVEMENT
            # =================================================

            if (
                row[
                    "r_quantity"
                ]
                > 0
            ):

                before = int(
                    stock.r_stock
                    or 0
                )

                stock.r_stock = (
                    before
                    - row[
                        "r_quantity"
                    ]
                )

                after = int(
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
                        before,

                    quantity_after=
                        after,

                    reference_type=
                        "SALE",

                    reference_id=
                        sale.id,

                    reference_number=
                        sale.invoice_number,

                    reason=
                        None,

                    notes=(
                        "Stock delivered "
                        "through billing."
                    ),
                )

            # =================================================
            # SALE ITEM
            # =================================================

            sale_item = SaleItem(
                sale_id=
                    sale.id,

                variant_id=
                    row[
                        "variant_id"
                    ],

                quantity=
                    row[
                        "quantity"
                    ],

                stock_type=
                    row[
                        "stock_type"
                    ],

                k_quantity=
                    row[
                        "k_quantity"
                    ],

                r_quantity=
                    row[
                        "r_quantity"
                    ],

                cost_price=
                    row[
                        "cost_price"
                    ],

                unit_price=
                    row[
                        "unit_price"
                    ],

                discount=
                    row[
                        "discount"
                    ],

                gst=
                    row[
                        "gst"
                    ],

                total_price=
                    row[
                        "total_price"
                    ],
            )

            db.add(
                sale_item
            )

        # ==================================================
        # CREATE BILL
        # ==================================================

        bill = Bill(
            sale_id=
                sale.id,

            shop_id=
                shop_id,

            customer_id=
                data.customer_id,

            invoice_number=
                invoice_number,

            subtotal=
                subtotal,

            discount=
                sale_discount,

            gst=
                gst_total,

            grand_total=
                grand_total,

            payment_method=
                payment_method,

            payment_status=
                "Pending",

            bill_status=(
                "Pending"
                if has_pending_items
                else "Completed"
            ),

            remarks=
                getattr(
                    data,
                    "remarks",
                    None,
                ),
        )

        db.add(
            bill
        )

        db.flush()

        # ==================================================
        # BILL ITEMS
        # ==================================================

        for row in (
            bill_item_data
        ):

            bill_item = BillItem(
                bill_id=
                    bill.id,

                variant_id=
                    row[
                        "variant_id"
                    ],

                ordered_qty=
                    row[
                        "ordered_qty"
                    ],

                delivered_qty=
                    row[
                        "delivered_qty"
                    ],

                pending_qty=
                    row[
                        "pending_qty"
                    ],

                k_quantity=
                    row[
                        "k_quantity"
                    ],

                r_quantity=
                    row[
                        "r_quantity"
                    ],

                k_delivered_qty=
                    row[
                        "k_delivered_qty"
                    ],

                r_delivered_qty=
                    row[
                        "r_delivered_qty"
                    ],

                selling_price=
                    row[
                        "selling_price"
                    ],

                discount=
                    row[
                        "discount"
                    ],

                gst_percentage=
                    row[
                        "gst_percentage"
                    ],

                gst=
                    row[
                        "gst"
                    ],

                total=
                    row[
                        "total"
                    ],

                item_status=
                    row[
                        "item_status"
                    ],
            )

            db.add(
                bill_item
            )

        # ==================================================
        # PAYMENTS
        # ==================================================

        for payment_data in (
            data.payments
        ):

            amount = to_money(
                payment_data.amount
            )

            if amount <= 0:
                continue

            payment = Payment(
                bill_id=
                    bill.id,

                amount=
                    amount,

                payment_method=
                    payment_data
                    .payment_mode,
            )

            db.add(
                payment
            )

        # ==================================================
        # PAYMENT STATUS
        # ==================================================

        bill.payment_status = (
            resolve_payment_status(
                total_paid=
                    total_paid,

                grand_total=
                    grand_total,
            )
        )

        # ==================================================
        # FULFILLMENT STATUS
        # ==================================================

        bill.bill_status = (
            resolve_bill_status(
                has_pending_items
            )
        )

        # ==================================================
        # COMMIT
        # ==================================================

        db.commit()

        db.refresh(
            bill
        )

        return get_bill_by_id(
            db=db,

            bill_id=
                bill.id,

            shop_id=
                shop_id,
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
    return (
        db.query(Bill)
        .options(
            joinedload(
                Bill.customer
            ),

            joinedload(
                Bill.sale
            ),

            joinedload(
                Bill.items
            ).joinedload(
                BillItem.variant
            ),

            joinedload(
                Bill.payments
            ),
        )
        .filter(
            Bill.shop_id
            == shop_id
        )
        .order_by(
            Bill.created_at
            .desc()
        )
        .all()
    )


# ==========================================================
# BILL DETAILS
# ==========================================================

def get_bill_by_id(
    db: Session,
    bill_id: int,
    shop_id: int,
):
    return (
        db.query(Bill)
        .options(
            joinedload(
                Bill.customer
            ),

            joinedload(
                Bill.sale
            ),

            joinedload(
                Bill.items
            ).joinedload(
                BillItem.variant
            ),

            joinedload(
                Bill.payments
            ),
        )
        .filter(
            Bill.id
            == bill_id,

            Bill.shop_id
            == shop_id,
        )
        .first()
    )


# ==========================================================
# SEARCH BILL
# ==========================================================

def search_bill(
    db: Session,
    shop_id: int,
    keyword: str,
):
    return (
        db.query(Bill)
        .options(
            joinedload(
                Bill.customer
            ),

            joinedload(
                Bill.sale
            ),

            joinedload(
                Bill.items
            ).joinedload(
                BillItem.variant
            ),

            joinedload(
                Bill.payments
            ),
        )
        .outerjoin(
            Customer
        )
        .filter(
            Bill.shop_id
            == shop_id
        )
        .filter(
            or_(
                Bill.invoice_number
                .ilike(
                    f"%{keyword}%"
                ),

                Customer
                .customer_name
                .ilike(
                    f"%{keyword}%"
                ),
            )
        )
        .order_by(
            Bill.created_at
            .desc()
        )
        .all()
    )
