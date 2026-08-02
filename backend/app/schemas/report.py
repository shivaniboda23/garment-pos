from decimal import Decimal
from pydantic import BaseModel


class ProfitLossResponse(BaseModel):
    total_sales: Decimal
    sales_return: Decimal

    net_sales: Decimal

    total_purchase: Decimal
    purchase_return: Decimal

    net_purchase: Decimal

    gross_profit: Decimal

    total_expense: Decimal

    net_profit: Decimal

    profit_margin: float


class DailyReportResponse(BaseModel):
    date: str

    sales: Decimal

    purchase: Decimal

    expense: Decimal

    profit: Decimal


class MonthlyReportResponse(BaseModel):
    month: str

    sales: Decimal

    purchase: Decimal

    expense: Decimal

    profit: Decimal