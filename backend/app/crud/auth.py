from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shop import Shop
from app.models.user import User

from app.core.enums import UserRole
from app.core.security import (
    hash_password,
    verify_password,
)


def register_shop(db: Session, data):

    existing = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing:
        raise Exception("Email already registered")

    shop = Shop(
        shop_name=data.shop_name,
        owner_name=data.owner_name,
        phone=data.phone,
        email=data.email,
    )

    db.add(shop)
    db.flush()

    admin = User(
        shop_id=shop.id,
        full_name=data.owner_name,
        email=data.email,
        password=hash_password(data.password),
        role=UserRole.ADMIN,
    )

    db.add(admin)

    db.commit()

    db.refresh(shop)

    return shop


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user