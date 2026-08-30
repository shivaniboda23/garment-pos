from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.sale_return import SaleReturn
from app.models.sale_return_item import SaleReturnItem
from app.models.stock import Stock
from app.models.supplier import Supplier
from app.models.expense import Expense


# ==========================================================
# DASHBOARD COGS HELPERS
# ==========================================================

def _get_cogs_for_date(
    db: Session,
    shop_id: int,
    target_date: date,
):
    sales = (
        db.query(Sale.id)
        .filter(
            Sale.shop_id == shop_id,
            func.date(
                Sale.created_at
            ) == target_date,
        )
        .all()
    )

    sale_ids = [
        row.id
        for row in sales
    ]

    if not sale_ids:
        return Decimal("0.00")

    sale_items = (
        db.query(SaleItem)
        .filter(
            SaleItem.sale_id.in_(sale_ids)
        )
        .all()
    )

    total_cogs = Decimal("0.00")

    for item in sale_items:
        total_cogs += (
            Decimal(
                str(item.cost_price or 0)
            )
            * Decimal(item.quantity)
        )

    returned_rows = (
        db.query(
            SaleReturnItem,
            SaleItem.cost_price,
        )
        .join(
            SaleReturn,
            SaleReturnItem.sale_return_id
            == SaleReturn.id,
        )
        .join(
            SaleItem,
            (
                SaleItem.sale_id
                == SaleReturn.sale_id
            )
            & (
                SaleItem.variant_id
                == SaleReturnItem.variant_id
            ),
        )
        .filter(
            SaleReturn.shop_id == shop_id,
            SaleReturn.status == "Completed",
            SaleReturn.sale_id.in_(sale_ids),
        )
        .all()
    )

    returned_cogs = Decimal("0.00")

    for return_item, cost_price in returned_rows:
        returned_cogs += (
            Decimal(
                str(cost_price or 0)
            )
            * Decimal(return_item.quantity)
        )

    net_cogs = (
        total_cogs
        - returned_cogs
    )

    if net_cogs < 0:
        return Decimal("0.00")

    return net_cogs


# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

def get_dashboard_summary(
    db: Session,
    shop_id: int,
):
    today = date.today()

    today_sales = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Sale.total_amount
                    ),
                    0,
                )
            )
            .filter(
                Sale.shop_id == shop_id,
                func.date(
                    Sale.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    today_sales_return = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        SaleReturn.refund_amount
                    ),
                    0,
                )
            )
            .filter(
                SaleReturn.shop_id == shop_id,
                SaleReturn.status == "Completed",
                func.date(
                    SaleReturn.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    today_purchase = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Purchase.grand_total
                    ),
                    0,
                )
            )
            .filter(
                Purchase.shop_id == shop_id,
                func.date(
                    Purchase.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    today_purchase_return = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        PurchaseReturn.total_amount
                    ),
                    0,
                )
            )
            .filter(
                PurchaseReturn.shop_id == shop_id,
                PurchaseReturn.status == "Completed",
                func.date(
                    PurchaseReturn.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    today_expense = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Expense.amount
                    ),
                    0,
                )
            )
            .filter(
                Expense.shop_id == shop_id,
                func.date(
                    Expense.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    today_net_sales = (
        today_sales
        - today_sales_return
    )

    today_cogs = _get_cogs_for_date(
        db=db,
        shop_id=shop_id,
        target_date=today,
    )

    today_gross_profit = (
        today_net_sales
        - today_cogs
    )

    today_profit = (
        today_gross_profit
        - today_expense
    )

    total_products = (
        db.query(Product)
        .filter(
            Product.shop_id == shop_id
        )
        .count()
    )

    total_customers = (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id
        )
        .count()
    )

    total_suppliers = (
        db.query(Supplier)
        .filter(
            Supplier.shop_id == shop_id
        )
        .count()
    )

    low_stock_products = (
        db.query(Stock)
        .join(ProductVariant)
        .join(Product)
        .filter(
            Product.shop_id == shop_id,
            (
                Stock.k_stock
                + Stock.r_stock
            ) <= ProductVariant.reorder_level,
        )
        .count()
    )

    pending_purchase_payments = (
        db.query(Purchase)
        .filter(
            Purchase.shop_id == shop_id,
            Purchase.balance_amount > 0,
        )
        .count()
    )

    return {
        "today_sales": today_sales,
        "today_sales_return": today_sales_return,
        "today_net_sales": today_net_sales,
        "today_purchase": today_purchase,
        "today_purchase_return": today_purchase_return,
        "today_net_purchase": (
            today_purchase
            - today_purchase_return
        ),
        "today_cogs": today_cogs,
        "today_gross_profit": today_gross_profit,
        "today_expense": today_expense,
        "today_profit": today_profit,
        "total_customers": total_customers,
        "total_suppliers": total_suppliers,
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "pending_purchase_payments": pending_purchase_payments,
    }


# ==========================================================
# LOW STOCK
# ==========================================================

def get_low_stock_products(
    db: Session,
    shop_id: int,
):
    result = (
        db.query(
            Product.id.label("product_id"),
            Product.product_name,
            ProductVariant.id.label("variant_id"),
            ProductVariant.sku,
            Stock.k_stock,
            Stock.r_stock,
            (
                Stock.k_stock
                + Stock.r_stock
            ).label("total_stock"),
            ProductVariant.reorder_level,
        )
        .select_from(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .join(
            Stock,
            Stock.variant_id == ProductVariant.id,
        )
        .filter(
            Product.shop_id == shop_id,
            (
                Stock.k_stock
                + Stock.r_stock
            ) <= ProductVariant.reorder_level,
        )
        .order_by(
            (
                Stock.k_stock
                + Stock.r_stock
            ).asc()
        )
        .all()
    )

    return [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "variant_id": row.variant_id,
            "sku": row.sku,
            "k_stock": row.k_stock,
            "r_stock": row.r_stock,
            "total_stock": row.total_stock,
            "reorder_level": row.reorder_level,
        }
        for row in result
    ]


# ==========================================================
# TOP SELLING PRODUCTS
# ==========================================================

def get_top_selling_products(
    db: Session,
    shop_id: int,
):
    result = (
        db.query(
            Product.product_name,
            ProductVariant.sku,
            func.sum(
                SaleItem.quantity
            ).label("quantity_sold"),
        )
        .join(
            ProductVariant,
            Product.id == ProductVariant.product_id,
        )
        .join(
            SaleItem,
            ProductVariant.id == SaleItem.variant_id,
        )
        .join(
            Sale,
            Sale.id == SaleItem.sale_id,
        )
        .filter(
            Sale.shop_id == shop_id,
        )
        .group_by(
            Product.product_name,
            ProductVariant.sku,
        )
        .order_by(
            func.sum(
                SaleItem.quantity
            ).desc()
        )
        .limit(10)
        .all()
    )

    return [
        {
            "product_name": row.product_name,
            "sku": row.sku,
            "quantity_sold": int(
                row.quantity_sold
            ),
        }
        for row in result
    ]


# ==========================================================
# RECENT SALES
# ==========================================================

def get_recent_sales(
    db: Session,
    shop_id: int,
):
    return (
        db.query(Sale)
        .options(
            joinedload(Sale.customer)
        )
        .filter(
            Sale.shop_id == shop_id,
        )
        .order_by(
            Sale.created_at.desc()
        )
        .limit(10)
        .all()
    )


# ==========================================================
# RECENT PURCHASES
# ==========================================================

def get_recent_purchases(
    db: Session,
    shop_id: int,
):
    return (
        db.query(Purchase)
        .options(
            joinedload(Purchase.supplier)
        )
        .filter(
            Purchase.shop_id == shop_id,
        )
        .order_by(
            Purchase.created_at.desc()
        )
        .limit(10)
        .all()
    )


# ==========================================================
# MONTHLY SALES
# ==========================================================

def get_monthly_sales(
    db: Session,
    shop_id: int,
):
    result = (
        db.query(
            func.to_char(
                Sale.created_at,
                "Mon YYYY",
            ).label("month"),
            func.sum(
                Sale.total_amount
            ).label("sales"),
        )
        .filter(
            Sale.shop_id == shop_id,
        )
        .group_by(
            func.to_char(
                Sale.created_at,
                "Mon YYYY",
            )
        )
        .order_by(
            func.min(
                Sale.created_at
            )
        )
        .all()
    )

    return [
        {
            "month": row.month,
            "sales": float(
                row.sales or 0
            ),
        }
        for row in result
    ]