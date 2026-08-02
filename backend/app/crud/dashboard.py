from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stock import Stock
from app.models.supplier import Supplier


# ==========================================================
# Dashboard Summary
# ==========================================================

def get_dashboard_summary(
    db: Session,
    shop_id: int,
):

    today = date.today()

    today_sales = (
        db.query(func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(
            Sale.shop_id == shop_id,
            func.date(Sale.created_at) == today,
        )
        .scalar()
    )

    today_purchase = (
        db.query(func.coalesce(func.sum(Purchase.grand_total), 0))
        .filter(
            Purchase.shop_id == shop_id,
            func.date(Purchase.created_at) == today,
        )
        .scalar()
    )

    total_products = (
        db.query(Product)
        .filter(Product.shop_id == shop_id)
        .count()
    )

    total_customers = (
        db.query(Customer)
        .filter(Customer.shop_id == shop_id)
        .count()
    )

    total_suppliers = (
        db.query(Supplier)
        .filter(Supplier.shop_id == shop_id)
        .count()
    )

    low_stock_products = (
        db.query(Stock)
        .join(ProductVariant)
        .join(Product)
        .filter(
            Product.shop_id == shop_id,
            (
                Stock.k_stock + Stock.r_stock
            ) <= ProductVariant.reorder_level
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
        "today_purchase": today_purchase,
        "today_profit": today_sales - today_purchase,
        "total_customers": total_customers,
        "total_suppliers": total_suppliers,
        "total_products": total_products,
        "low_stock_products": low_stock_products,
        "pending_purchase_payments": pending_purchase_payments,
    }


# ==========================================================
# Low Stock
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
                Stock.k_stock +
                Stock.r_stock
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
                Stock.k_stock +
                Stock.r_stock
            ) <= ProductVariant.reorder_level,
        )
        .order_by(
            (
                Stock.k_stock +
                Stock.r_stock
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
# Top Selling Products
# ==========================================================

def get_top_selling_products(
    db: Session,
    shop_id: int,
):

    result = (
        db.query(
            Product.product_name,
            ProductVariant.sku,
            func.sum(SaleItem.quantity).label("quantity_sold"),
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
            func.sum(SaleItem.quantity).desc()
        )
        .limit(10)
        .all()
    )

    return [
        {
            "product_name": row.product_name,
            "sku": row.sku,
            "quantity_sold": int(row.quantity_sold),
        }
        for row in result
    ]


# ==========================================================
# Recent Sales
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
# Recent Purchases
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
# Monthly Sales
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
            func.min(Sale.created_at)
        )
        .all()
    )

    return [
        {
            "month": row.month,
            "sales": float(row.sales),
        }
        for row in result
    ]