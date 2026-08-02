from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel


# ============================================
# Dashboard Summary
# ============================================

class DashboardSummary(BaseModel):
    today_sales: Decimal
    today_purchase: Decimal
    today_profit: Decimal

    total_customers: int
    total_suppliers: int
    total_products: int

    low_stock_products: int
    pending_purchase_payments: int


# ============================================
# Low Stock
# ============================================

class LowStockResponse(BaseModel):
    product_id: int
    product_name: str

    variant_id: int
    sku: str

    quantity: int
    reorder_level: int


# ============================================
# Top Selling Products
# ============================================

class TopSellingProduct(BaseModel):
    product_name: str
    sku: str
    quantity_sold: int


# ============================================
# Recent Sales
# ============================================

class RecentSale(BaseModel):
    sale_id: int
    invoice_number: str

    customer_name: str | None

    total_amount: Decimal

    created_at: datetime


# ============================================
# Recent Purchases
# ============================================

class RecentPurchase(BaseModel):
    purchase_id: int

    invoice_number: str

    supplier_name: str

    grand_total: Decimal

    created_at: datetime


# ============================================
# Monthly Sales
# ============================================

class MonthlySales(BaseModel):
    month: str
    sales: Decimal