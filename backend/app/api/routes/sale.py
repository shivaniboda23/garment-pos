from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.database import get_db

from app.crud.sale import (
    create_sale,
    get_all_sales,
    get_sale_by_id,
)

from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
)

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# =====================================================
# CREATE SALE
# =====================================================

@router.post(
    "",
    response_model=SaleResponse,
)
def add_sale(
    request: SaleCreate,
    db: Session = Depends(get_db),
):

    sale = create_sale(
        db,
        request,
    )

    if sale is None:

        raise HTTPException(
            status_code=404,
            detail="Shop or Customer not found",
        )

    return sale


# =====================================================
# SALES HISTORY
# =====================================================

@router.get("/")
def sales_history(
    invoice: str | None = None,
    customer_id: int | None = None,
    date: str | None = None,
    db: Session = Depends(get_db),
):

    shop_id = 3

    sales = get_all_sales(
        db=db,
        shop_id=shop_id,
        invoice=invoice,
        customer_id=customer_id,
        date=date,
    )

    return sales


# =====================================================
# SALE DETAILS
# =====================================================

@router.get("/{sale_id}")
def sale_details(
    sale_id: int,
    db: Session = Depends(get_db),
):

    shop_id = 3

    sale = get_sale_by_id(
        db=db,
        sale_id=sale_id,
        shop_id=shop_id,
    )

    if not sale:

        raise HTTPException(
            status_code=404,
            detail="Sale not found",
        )

    return sale