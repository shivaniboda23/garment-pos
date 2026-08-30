from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.crud.report import (
    get_profit_loss,
    get_daily_report,
    get_monthly_report,
    get_product_analytics,
)

from app.schemas.report import (
    ProfitLossResponse,
    DailyReportResponse,
    MonthlyReportResponse,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# ==========================================================
# PROFIT & LOSS
# ==========================================================

@router.get(
    "/profit-loss",
    response_model=ProfitLossResponse,
)
def profit_loss(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_profit_loss(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# DAILY REPORT
# ==========================================================

@router.get(
    "/daily",
    response_model=DailyReportResponse,
)
def daily_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_daily_report(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# MONTHLY REPORT
# ==========================================================

@router.get(
    "/monthly",
    response_model=list[MonthlyReportResponse],
)
def monthly_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_monthly_report(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# PRODUCT ANALYTICS
# ==========================================================

@router.get(
    "/products",
)
def product_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_product_analytics(
        db=db,
        shop_id=current_user.shop_id,
    )