from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import TEMP_SHOP_ID

from app.schemas.sale_return import (
    SaleReturnCreate,
    SaleReturnResponse,
)

from app.crud.sale_return import (
    create_sale_return,
    get_all_sale_returns,
    get_sale_return_by_id,
)

router = APIRouter(
    prefix="/sale-return",
    tags=["Sale Return"],
)


# =====================================================
# CREATE SALE RETURN
# =====================================================

@router.post(
    "/create",
    response_model=SaleReturnResponse,
)
def create_sale_return_api(
    request: SaleReturnCreate,
    db: Session = Depends(get_db),
):

    shop_id = TEMP_SHOP_ID

    sale_return = create_sale_return(
        db=db,
        shop_id=shop_id,
        data=request,
    )

    return sale_return


# =====================================================
# SALE RETURN HISTORY
# =====================================================

@router.get("/")
def sale_return_history(
    db: Session = Depends(get_db),
):

    shop_id = TEMP_SHOP_ID

    returns = get_all_sale_returns(
        db=db,
        shop_id=shop_id,
    )

    return returns


# =====================================================
# SALE RETURN DETAILS
# =====================================================

@router.get("/{return_id}")
def sale_return_details(
    return_id: int,
    db: Session = Depends(get_db),
):

    shop_id = TEMP_SHOP_ID

    sale_return = get_sale_return_by_id(
        db=db,
        shop_id=shop_id,
        return_id=return_id,
    )

    if not sale_return:

        raise HTTPException(
            status_code=404,
            detail="Sale Return not found",
        )

    return sale_return