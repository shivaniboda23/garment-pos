from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.customer import Customer
from app.models.shop import Shop


def create_customer(
    db: Session,
    shop_id: int,
    data,
):
    # Check shop exists
    shop = (
        db.query(Shop)
        .filter(Shop.id == shop_id)
        .first()
    )

    if not shop:
        return None

    # Check duplicate phone
    existing_customer = (
        db.query(Customer)
        .filter(Customer.phone == data.phone)
        .first()
    )

    if existing_customer:
        return None

    customer = Customer(
        shop_id=shop_id,
        customer_name=data.customer_name,
        phone=data.phone,
        email=data.email,
        address=data.address,
        gst_number=data.gst_number,
    )

    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        return None

    return customer


def get_customers(
    db: Session,
    shop_id: int,
):
    return (
        db.query(Customer)
        .filter(
            Customer.shop_id == shop_id,
            Customer.is_active == True,
        )
        .all()
    )


def get_customer(
    db: Session,
    shop_id: int,
    customer_id: int,
):
    return (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.shop_id == shop_id,
        )
        .first()
    )


def update_customer(
    db: Session,
    shop_id: int,
    customer_id: int,
    data,
):
    customer = get_customer(
        db=db,
        shop_id=shop_id,
        customer_id=customer_id,
    )

    if not customer:
        return None

    update_data = data.model_dump(
        exclude_unset=True
    )

    # Prevent duplicate phone numbers
    if "phone" in update_data:
        existing = (
            db.query(Customer)
            .filter(
                Customer.phone == update_data["phone"],
                Customer.id != customer_id,
            )
            .first()
        )

        if existing:
            return None

    for key, value in update_data.items():
        setattr(
            customer,
            key,
            value,
        )

    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        return None

    return customer


def delete_customer(
    db: Session,
    shop_id: int,
    customer_id: int,
):
    customer = get_customer(
        db=db,
        shop_id=shop_id,
        customer_id=customer_id,
    )

    if not customer:
        return False

    customer.is_active = False

    db.commit()

    return True
