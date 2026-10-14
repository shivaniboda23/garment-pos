"""Create the first administrator only in a fresh, disposable staging database.

Run interactively from the backend directory after `alembic upgrade head`.
Never use this script on the existing Bhavani shop database.
"""

import argparse
from getpass import getpass

from sqlalchemy import func, select, text

from app.crud.auth import register_shop
from app.db.database import SessionLocal
from app.models.shop import Shop
from app.models.user import User
from app.schemas.auth import ShopRegisterRequest


def _validate_target(database_name, revision, shops, users, expected_name):
    if not expected_name.startswith("bhavani_staging_"):
        raise ValueError("Expected database name must start with bhavani_staging_.")
    if database_name != expected_name:
        raise ValueError("Connected database does not match --expected-db.")
    if revision != "b2e4f8a1c3d5":
        raise ValueError("Staging database is not at the reviewed Alembic head.")
    if shops != 0 or users != 0:
        raise ValueError("Staging database already has a shop or user.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-db", required=True)
    args = parser.parse_args()

    with SessionLocal() as db:
        _validate_target(
            database_name=db.scalar(text("SELECT current_database()")),
            revision=db.scalar(text("SELECT version_num FROM alembic_version")),
            shops=db.scalar(select(func.count()).select_from(Shop)),
            users=db.scalar(select(func.count()).select_from(User)),
            expected_name=args.expected_db,
        )

        print("Enter fictional staging shop details only. Do not use customer data.")
        shop_name = input("Shop name: ").strip()
        owner_name = input("Administrator name: ").strip()
        phone = input("Test phone: ").strip()
        email = input("Test email: ").strip()
        password = getpass("New staging password (at least 12 characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 12 or password != confirmation:
            raise ValueError("Passwords must match and be at least 12 characters.")

        request = ShopRegisterRequest(
            shop_name=shop_name,
            owner_name=owner_name,
            phone=phone,
            email=email,
            password=password,
        )
        shop = register_shop(db, request)
        print(f"Created staging shop {shop.id} in {args.expected_db}.")


if __name__ == "__main__":
    main()
