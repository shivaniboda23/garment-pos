from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.product_variant import ProductVariant
from app.models.product import Product

from app.models.bill import Bill
from app.models.payment import Payment
from app.models.purchase import Purchase
from app.models.customer import Customer


def get_notifications(
    db: Session,
    shop_id: int,
):
    notifications = []

    # ==========================================================
    # LOW STOCK
    #
    # One notification per affected variant.
    #
    # IMPORTANT:
    # A minimum value of 0 means "NOT CONFIGURED".
    # Therefore:
    #
    # K LOW only when:
    #   k_minimum_stock > 0
    #   AND
    #   k_stock <= k_minimum_stock
    #
    # R LOW only when:
    #   r_minimum_stock > 0
    #   AND
    #   r_stock <= r_minimum_stock
    #
    # TOTAL LOW only when:
    #   minimum_stock > 0
    #   AND
    #   total_stock <= minimum_stock
    # ==========================================================

    low_stock = (
        db.query(
            Product.id.label("product_id"),
            Product.product_name,
            ProductVariant.id.label("variant_id"),
            ProductVariant.sku,
            Stock.k_stock,
            Stock.r_stock,
            Stock.k_minimum_stock,
            Stock.r_minimum_stock,
            Stock.minimum_stock,
            Stock.maximum_stock,
        )
        .select_from(Product)
        .join(
            ProductVariant,
            ProductVariant.product_id == Product.id,
        )
        .join(
            Stock,
            Stock.variant_id == ProductVariant.id,
        )
        .filter(
            Product.shop_id == shop_id,
            ProductVariant.is_active.is_(True),
        )
        .all()
    )

    for item in low_stock:
        k_stock = int(
            item.k_stock or 0
        )

        r_stock = int(
            item.r_stock or 0
        )

        total_stock = (
            k_stock + r_stock
        )

        k_minimum = int(
            item.k_minimum_stock or 0
        )

        r_minimum = int(
            item.r_minimum_stock or 0
        )

        total_minimum = int(
            item.minimum_stock or 0
        )

        maximum_stock = int(
            item.maximum_stock or 0
        )

        # ------------------------------------------------------
        # IMPORTANT:
        # 0 minimum = not configured
        # ------------------------------------------------------

        k_configured = (
            k_minimum > 0
        )

        r_configured = (
            r_minimum > 0
        )

        total_configured = (
            total_minimum > 0
        )

        # ------------------------------------------------------
        # LOW STATUS
        # ------------------------------------------------------

        k_low = (
            k_configured
            and k_stock <= k_minimum
        )

        r_low = (
            r_configured
            and r_stock <= r_minimum
        )

        total_low = (
            total_configured
            and total_stock <= total_minimum
        )

        # ------------------------------------------------------
        # If nothing is configured as low, don't create
        # a notification.
        # ------------------------------------------------------

        if not (
            k_low
            or r_low
            or total_low
        ):
            continue

        # ------------------------------------------------------
        # Build list of low areas
        # ------------------------------------------------------

        low_parts = []

        if k_low:
            low_parts.append(
                "K"
            )

        if r_low:
            low_parts.append(
                "R"
            )

        if total_low:
            low_parts.append(
                "Total"
            )

        # ------------------------------------------------------
        # Title
        # ------------------------------------------------------

        if len(low_parts) == 1:
            title = (
                f"{low_parts[0]} Stock Low"
            )
        else:
            title = "Stock Low"

        # ------------------------------------------------------
        # Message
        # ------------------------------------------------------

        low_areas = ", ".join(
            low_parts
        )

        message = (
            f"{item.product_name} "
            f"({item.sku}) needs attention: "
            f"{low_areas} stock is below "
            f"the configured minimum."
        )

        # ------------------------------------------------------
        # Notification
        # ------------------------------------------------------

        notifications.append(
            {
                "type": "LOW_STOCK",
                "subtype": "VARIANT",

                "title": title,

                "message": message,

                "product_id":
                    item.product_id,

                "product_name":
                    item.product_name,

                "variant_id":
                    item.variant_id,

                "sku":
                    item.sku,

                # Current stock
                "k_stock":
                    k_stock,

                "r_stock":
                    r_stock,

                "total_stock":
                    total_stock,

                # Thresholds
                "k_minimum_stock":
                    k_minimum,

                "r_minimum_stock":
                    r_minimum,

                "minimum_stock":
                    total_minimum,

                "maximum_stock":
                    maximum_stock,

                # Configuration flags
                "k_configured":
                    k_configured,

                "r_configured":
                    r_configured,

                "total_configured":
                    total_configured,

                # Low flags
                "k_low":
                    k_low,

                "r_low":
                    r_low,

                "total_low":
                    total_low,
            }
        )

    # ==========================================================
    # CUSTOMER DUES
    #
    # Outstanding:
    #
    # Bill grand total
    # -
    # total payments
    # ==========================================================

    customer_dues = (
        db.query(
            Bill.id.label(
                "bill_id"
            ),
            Bill.invoice_number,
            Bill.customer_id,
            Bill.grand_total,
            func.coalesce(
                func.sum(
                    Payment.amount
                ),
                0,
            ).label(
                "paid_amount"
            ),
        )
        .select_from(Bill)
        .outerjoin(
            Payment,
            Payment.bill_id
            == Bill.id,
        )
        .filter(
            Bill.shop_id == shop_id,
            Bill.customer_id.isnot(
                None
            ),
        )
        .group_by(
            Bill.id,
            Bill.invoice_number,
            Bill.customer_id,
            Bill.grand_total,
        )
        .all()
    )

    for bill in customer_dues:
        grand_total = float(
            bill.grand_total or 0
        )

        paid_amount = float(
            bill.paid_amount or 0
        )

        due_amount = (
            grand_total
            - paid_amount
        )

        # Ignore fully paid bills.
        if due_amount <= 0.01:
            continue

        customer_name = (
            "Customer"
        )

        customer = (
            db.query(Customer)
            .filter(
                Customer.id
                == bill.customer_id
            )
            .first()
        )

        if customer:
            customer_name = (
                customer.customer_name
                or "Customer"
            )

        notifications.append(
            {
                "type":
                    "CUSTOMER_DUE",

                "title":
                    "Pending Customer Payment",

                "message": (
                    f"{customer_name} has "
                    f"₹{due_amount:.2f} pending "
                    f"on {bill.invoice_number}."
                ),

                "bill_id":
                    bill.bill_id,

                "invoice_number":
                    bill.invoice_number,

                "customer_id":
                    bill.customer_id,

                "customer_name":
                    customer_name,

                "grand_total":
                    grand_total,

                "paid_amount":
                    paid_amount,

                "due_amount":
                    due_amount,
            }
        )

    # ==========================================================
    # SUPPLIER DUES
    # ==========================================================

    supplier_dues = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
            Purchase.balance_amount > 0,
        )
        .all()
    )

    for purchase in supplier_dues:
        supplier_name = (
            "Supplier"
        )

        try:
            if purchase.supplier:
                supplier_name = (
                    purchase.supplier.supplier_name
                    or "Supplier"
                )
        except Exception:
            supplier_name = "Supplier"

        balance_amount = float(
            purchase.balance_amount
            or 0
        )

        if balance_amount <= 0:
            continue

        notifications.append(
            {
                "type":
                    "SUPPLIER_DUE",

                "title":
                    "Supplier Payment Pending",

                "message": (
                    f"{supplier_name} has "
                    f"₹{balance_amount:.2f} pending "
                    f"on {purchase.invoice_number}."
                ),

                "purchase_id":
                    purchase.id,

                "invoice_number":
                    purchase.invoice_number,

                "supplier_id":
                    purchase.supplier_id,

                "supplier_name":
                    supplier_name,

                "grand_total":
                    float(
                        purchase.grand_total
                        or 0
                    ),

                "paid_amount":
                    float(
                        purchase.paid_amount
                        or 0
                    ),

                "due_amount":
                    balance_amount,
            }
        )

    return notifications