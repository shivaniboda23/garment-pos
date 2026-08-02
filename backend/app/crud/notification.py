from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.stock import Stock
from app.models.product_variant import ProductVariant
from app.models.product import Product

from app.models.sale import Sale
from app.models.purchase import Purchase


def get_notifications(
    db: Session,
    shop_id: int,
):

    notifications = []

    # -----------------------------
    # LOW STOCK
    # -----------------------------

    low_stock = (
        db.query(
            Product.product_name,
            ProductVariant.sku,
            Stock.r_stock,
            ProductVariant.reorder_level,
        )
        .join(ProductVariant)
        .join(Product)
        .filter(
            Product.shop_id == shop_id,
            Stock.r_stock <= ProductVariant.reorder_level,
        )
        .all()
    )

    for item in low_stock:

        notifications.append(
            {
                "type": "LOW_STOCK",
                "title": "Low Stock",
                "message": (
                    f"{item.product_name} "
                    f"({item.sku}) has only "
                    f"{item.r_stock} pieces remaining."
                ),
            }
        )

    # -----------------------------
    # CUSTOMER DUES
    # -----------------------------

    dues = (
        db.query(Sale)
        .filter(
            Sale.shop_id == shop_id,
            Sale.balance_amount > 0,
        )
        .all()
    )

    for sale in dues:

        notifications.append(
            {
                "type": "CUSTOMER_DUE",
                "title": "Pending Customer Payment",
                "message": (
                    f"Bill #{sale.bill_number} "
                    f"Pending ₹{sale.balance_amount}"
                ),
            }
        )

    # -----------------------------
    # SUPPLIER DUES
    # -----------------------------

    supplier_dues = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
            Purchase.balance_amount > 0,
        )
        .all()
    )

    for purchase in supplier_dues:

        notifications.append(
            {
                "type": "SUPPLIER_DUE",
                "title": "Supplier Payment Pending",
                "message": (
                    f"Purchase #{purchase.invoice_number} "
                    f"Pending ₹{purchase.balance_amount}"
                ),
            }
        )

    return notifications