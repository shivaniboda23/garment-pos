from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.sale_return import SaleReturn
from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn
from app.models.expense import Expense


# ==========================================================
# PROFIT & LOSS
# ==========================================================

def get_profit_loss(
    db: Session,
    shop_id: int,
):

    total_sales = (
        db.query(func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(Sale.shop_id == shop_id)
        .scalar()
    )

    # ✅ FIXED
    sales_return = (
        db.query(func.coalesce(func.sum(SaleReturn.refund_amount), 0))
        .filter(SaleReturn.shop_id == shop_id)
        .scalar()
    )

    total_purchase = (
        db.query(func.coalesce(func.sum(Purchase.grand_total), 0))
        .filter(Purchase.shop_id == shop_id)
        .scalar()
    )

    # ⚠️ Check your PurchaseReturn model.
    # If it has grand_total, replace total_amount with grand_total.
    purchase_return = (
        db.query(func.coalesce(func.sum(PurchaseReturn.total_amount), 0))
        .filter(PurchaseReturn.shop_id == shop_id)
        .scalar()
    )

    total_expense = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.shop_id == shop_id)
        .scalar()
    )

    net_sales = total_sales - sales_return
    net_purchase = total_purchase - purchase_return
    gross_profit = net_sales - net_purchase
    net_profit = gross_profit - total_expense

    profit_margin = (
        round((net_profit / net_sales) * 100, 2)
        if net_sales > 0
        else 0
    )

    return {
        "total_sales": float(total_sales),
        "sales_return": float(sales_return),
        "net_sales": float(net_sales),
        "total_purchase": float(total_purchase),
        "purchase_return": float(purchase_return),
        "net_purchase": float(net_purchase),
        "gross_profit": float(gross_profit),
        "total_expense": float(total_expense),
        "net_profit": float(net_profit),
        "profit_margin": profit_margin,
    }


# ==========================================================
# DAILY REPORT
# ==========================================================

def get_daily_report(
    db: Session,
    shop_id: int,
):

    today = date.today()

    sales = (
        db.query(func.coalesce(func.sum(Sale.total_amount), 0))
        .filter(
            Sale.shop_id == shop_id,
            func.date(Sale.created_at) == today,
        )
        .scalar()
    )

    purchase = (
        db.query(func.coalesce(func.sum(Purchase.grand_total), 0))
        .filter(
            Purchase.shop_id == shop_id,
            func.date(Purchase.created_at) == today,
        )
        .scalar()
    )

    expense = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.shop_id == shop_id,
            func.date(Expense.created_at) == today,
        )
        .scalar()
    )

    return {
        "date": str(today),
        "sales": float(sales),
        "purchase": float(purchase),
        "expense": float(expense),
        "profit": float(sales - purchase - expense),
    }


# ==========================================================
# MONTHLY REPORT
# ==========================================================

def get_monthly_report(
    db: Session,
    shop_id: int,
):

    sales = (
        db.query(
            func.to_char(
                Sale.created_at,
                "Mon YYYY",
            ).label("month"),
            func.sum(
                Sale.total_amount,
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
                Sale.created_at,
            )
        )
        .all()
    )

    purchase = (
        db.query(
            func.to_char(
                Purchase.created_at,
                "Mon YYYY",
            ).label("month"),
            func.sum(
                Purchase.grand_total,
            ).label("purchase"),
        )
        .filter(
            Purchase.shop_id == shop_id,
        )
        .group_by(
            func.to_char(
                Purchase.created_at,
                "Mon YYYY",
            )
        )
        .all()
    )

    expense = (
        db.query(
            func.to_char(
                Expense.created_at,
                "Mon YYYY",
            ).label("month"),
            func.sum(
                Expense.amount,
            ).label("expense"),
        )
        .filter(
            Expense.shop_id == shop_id,
        )
        .group_by(
            func.to_char(
                Expense.created_at,
                "Mon YYYY",
            )
        )
        .all()
    )

    purchase_map = {
        row.month: float(row.purchase)
        for row in purchase
    }

    expense_map = {
        row.month: float(row.expense)
        for row in expense
    }

    report = []

    for row in sales:

        s = float(row.sales)
        p = purchase_map.get(row.month, 0.0)
        e = expense_map.get(row.month, 0.0)

        report.append(
            {
                "month": row.month,
                "sales": s,
                "purchase": p,
                "expense": e,
                "profit": s - p - e,
            }
        )

    return report