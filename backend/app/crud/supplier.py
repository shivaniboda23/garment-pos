from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.supplier import Supplier

from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
)


# ==========================================================
# GENERATE SUPPLIER CODE
#
# SUP0001
# SUP0002
# ==========================================================

def generate_supplier_code(
    db: Session,
):

    last_supplier = (
        db.query(
            func.max(
                Supplier.id
            )
        )
        .scalar()
    )

    if last_supplier is None:
        number = 1

    else:
        number = (
            last_supplier
            + 1
        )

    return (
        f"SUP{number:04d}"
    )


# ==========================================================
# CREATE SUPPLIER / TAILOR
# ==========================================================

def create_supplier(
    db: Session,
    shop_id: int,
    supplier: SupplierCreate,
):

    new_supplier = Supplier(

        shop_id=
            shop_id,

        supplier_code=
            generate_supplier_code(
                db
            ),

        supplier_name=
            supplier.supplier_name,

        supplier_type=
            supplier.supplier_type,

        contact_person=
            supplier.contact_person,

        mobile=
            supplier.mobile,

        email=
            supplier.email,

        gst_number=
            supplier.gst_number,

        pan_number=
            supplier.pan_number,

        address=
            supplier.address,

        city=
            supplier.city,

        state=
            supplier.state,

        pincode=
            supplier.pincode,

        opening_balance=
            supplier.opening_balance,

        payment_terms=
            supplier.payment_terms,

        credit_limit=
            supplier.credit_limit,

        upi_id=
            supplier.upi_id,

        bank_name=
            supplier.bank_name,

        account_number=
            supplier.account_number,

        ifsc_code=
            supplier.ifsc_code,

        notes=
            supplier.notes,

        is_active=
            True,
    )

    try:

        db.add(
            new_supplier
        )

        db.commit()

        db.refresh(
            new_supplier
        )

        return new_supplier

    except Exception:

        db.rollback()
        raise


# ==========================================================
# LIST ALL ACTIVE SUPPLIERS / TAILORS
# ==========================================================

def get_suppliers(
    db: Session,
    shop_id: int,
):

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            == True,
        )
        .order_by(
            Supplier.supplier_name
        )
        .all()
    )


# ==========================================================
# LIST PRODUCT SUPPLIERS
#
# Used later if we want Purchase screens to display only:
# SUPPLIER + BOTH.
# ==========================================================

def get_product_suppliers(
    db: Session,
    shop_id: int,
):

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            == True,

            Supplier.supplier_type
            .in_(
                [
                    "SUPPLIER",
                    "BOTH",
                ]
            ),
        )
        .order_by(
            Supplier.supplier_name
        )
        .all()
    )


# ==========================================================
# LIST TAILORS
#
# Only TAILOR + BOTH.
# ==========================================================

def get_tailors(
    db: Session,
    shop_id: int,
):

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            == True,

            Supplier.supplier_type
            .in_(
                [
                    "TAILOR",
                    "BOTH",
                ]
            ),
        )
        .order_by(
            Supplier.supplier_name
        )
        .all()
    )


# ==========================================================
# GET SUPPLIER
# ==========================================================

def get_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
):

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.id
            == supplier_id,

            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            == True,
        )
        .first()
    )


# ==========================================================
# SEARCH SUPPLIER
# ==========================================================

def search_supplier(
    db: Session,
    shop_id: int,
    keyword: str,
):

    search_value = (
        f"%{keyword.strip()}%"
    )

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            == True,
        )
        .filter(
            (
                Supplier
                .supplier_name
                .ilike(
                    search_value
                )
            )
            |
            (
                Supplier
                .mobile
                .ilike(
                    search_value
                )
            )
            |
            (
                Supplier
                .supplier_code
                .ilike(
                    search_value
                )
            )
            |
            (
                Supplier
                .supplier_type
                .ilike(
                    search_value
                )
            )
        )
        .order_by(
            Supplier.supplier_name
        )
        .all()
    )


# ==========================================================
# UPDATE SUPPLIER / TAILOR
# ==========================================================

def update_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
    supplier: SupplierUpdate,
):

    db_supplier = (
        get_supplier(
            db=db,
            supplier_id=
                supplier_id,
            shop_id=
                shop_id,
        )
    )

    if not db_supplier:
        return None

    update_data = (
        supplier.model_dump(
            exclude_unset=True
        )
    )

    for (
        key,
        value,
    ) in update_data.items():

        setattr(
            db_supplier,
            key,
            value,
        )

    try:

        db.commit()

        db.refresh(
            db_supplier
        )

        return db_supplier

    except Exception:

        db.rollback()
        raise


# ==========================================================
# SOFT DELETE SUPPLIER
# ==========================================================

def delete_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
):

    supplier = (
        get_supplier(
            db=db,
            supplier_id=
                supplier_id,
            shop_id=
                shop_id,
        )
    )

    if not supplier:
        return None

    supplier.is_active = (
        False
    )

    try:

        db.commit()

        db.refresh(
            supplier
        )

        return supplier

    except Exception:

        db.rollback()
        raise