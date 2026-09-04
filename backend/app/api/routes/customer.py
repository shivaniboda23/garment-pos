from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)

from app.crud.customer import (
    create_customer,
    get_customers,
    get_customer,
    update_customer,
    delete_customer,
)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    customer = create_customer(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )

    if customer is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid customer data or "
                "phone number already exists"
            ),
        )

    return customer


@router.get(
    "/shop/{shop_id}",
    response_model=list[CustomerResponse],
)
def list_customers(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_customers(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    customer = get_customer(
        db=db,
        shop_id=current_user.shop_id,
        customer_id=customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def edit_customer(
    customer_id: int,
    request: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    customer = update_customer(
        db=db,
        shop_id=current_user.shop_id,
        customer_id=customer_id,
        data=request,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found or phone already exists",
        )

    return customer


@router.delete(
    "/{customer_id}",
)
def remove_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = delete_customer(
        db=db,
        shop_id=current_user.shop_id,
        customer_id=customer_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return {
        "message": "Customer deleted successfully"
    }
