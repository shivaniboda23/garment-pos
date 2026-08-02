from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db

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
):
    customer = create_customer(
        db,
        request,
    )

    if customer is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid shop or phone number already exists",
        )

    return customer


@router.get(
    "/shop/{shop_id}",
    response_model=list[CustomerResponse],
)
def list_customers(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_customers(
        db,
        shop_id,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = get_customer(
        db,
        customer_id,
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
):
    customer = update_customer(
        db,
        customer_id,
        request,
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
):
    success = delete_customer(
        db,
        customer_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return {
        "message": "Customer deleted successfully"
    }