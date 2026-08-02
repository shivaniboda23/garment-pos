from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.crud.dashboard import (
    get_dashboard_summary,
    get_low_stock_products,
    get_top_selling_products,
    get_recent_sales,
    get_recent_purchases,
    get_monthly_sales,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# =====================================================
# Dashboard Summary
# =====================================================

@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_dashboard_summary(
        db=db,
        shop_id=shop_id,
    )


# =====================================================
# Low Stock Products
# =====================================================

@router.get("/low-stock")
def low_stock_products(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_low_stock_products(
        db=db,
        shop_id=shop_id,
    )


# =====================================================
# Top Selling Products
# =====================================================

@router.get("/top-selling")
def top_selling_products(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_top_selling_products(
        db=db,
        shop_id=shop_id,
    )


# =====================================================
# Recent Sales
# =====================================================

@router.get("/recent-sales")
def recent_sales(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_recent_sales(
        db=db,
        shop_id=shop_id,
    )


# =====================================================
# Recent Purchases
# =====================================================

@router.get("/recent-purchases")
def recent_purchases(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_recent_purchases(
        db=db,
        shop_id=shop_id,
    )


# =====================================================
# Monthly Sales
# =====================================================

@router.get("/monthly-sales")
def monthly_sales(
    db: Session = Depends(get_db),
):

    shop_id = 3

    return get_monthly_sales(
        db=db,
        shop_id=shop_id,
    )