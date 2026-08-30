from decimal import Decimal

from pydantic import BaseModel


# ==========================================================
# PROFIT & LOSS RESPONSE
# ==========================================================

class ProfitLossResponse(BaseModel):
    total_sales: Decimal
    sales_return: Decimal
    net_sales: Decimal

    total_purchase: Decimal
    purchase_return: Decimal
    net_purchase: Decimal

    cogs: Decimal
    gross_profit: Decimal

    operating_expense: Decimal
    tailoring_expense: Decimal
    total_expense: Decimal
    net_profit: Decimal

    profit_margin: float

    zero_cost_sale_items: int


# ==========================================================
# DAILY REPORT
# ==========================================================

class DailyReportResponse(BaseModel):
    date: str

    sales: Decimal
    sales_return: Decimal
    net_sales: Decimal

    purchase: Decimal
    purchase_return: Decimal
    net_purchase: Decimal

    cogs: Decimal
    operating_expense: Decimal
    tailoring_expense: Decimal
    expense: Decimal

    gross_profit: Decimal
    profit: Decimal

    zero_cost_sale_items: int


# ==========================================================
# MONTHLY REPORT
# ==========================================================

class MonthlyReportResponse(BaseModel):
    month: str

    sales: Decimal
    sales_return: Decimal
    net_sales: Decimal

    purchase: Decimal
    purchase_return: Decimal
    net_purchase: Decimal

    cogs: Decimal
    operating_expense: Decimal
    tailoring_expense: Decimal
    expense: Decimal

    gross_profit: Decimal
    profit: Decimal

    zero_cost_sale_items: int