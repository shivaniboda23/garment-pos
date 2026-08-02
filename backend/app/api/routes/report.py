from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.crud.report import (
    get_profit_loss,
    get_daily_report,
    get_monthly_report,
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
# Profit & Loss
# ==========================================================

@router.get(
    "/profit-loss",
    response_model=ProfitLossResponse,
)
def profit_loss(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_profit_loss(
        db,
        shop_id,
    )


# ==========================================================
# Daily Report
# ==========================================================

@router.get(
    "/daily",
    response_model=DailyReportResponse,
)
def daily_report(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_daily_report(
        db,
        shop_id,
    )


# ==========================================================
# Monthly Report
# ==========================================================

@router.get(
    "/monthly",
    response_model=list[MonthlyReportResponse],
)
def monthly_report(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_monthly_report(
        db,
        shop_id,
    )