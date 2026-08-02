from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


# ----------------------------------------------------
# Generate Supplier Code
# SUP0001
# SUP0002
# ----------------------------------------------------
def generate_supplier_code(db: Session):

    last_supplier = (
        db.query(func.max(Supplier.id))
        .scalar()
    )

    if last_supplier is None:
        number = 1
    else:
        number = last_supplier + 1

    return f"SUP{number:04d}"


# ----------------------------------------------------
# Create Supplier
# ----------------------------------------------------
def create_supplier(
    db: Session,
    shop_id: int,
    supplier: SupplierCreate,
):

    new_supplier = Supplier(
        shop_id=shop_id,
        supplier_code=generate_supplier_code(db),

        supplier_name=supplier.supplier_name,
        contact_person=supplier.contact_person,

        mobile=supplier.mobile,
        email=supplier.email,

        gst_number=supplier.gst_number,
        pan_number=supplier.pan_number,

        address=supplier.address,
        city=supplier.city,
        state=supplier.state,
        pincode=supplier.pincode,

        opening_balance=supplier.opening_balance,

        payment_terms=supplier.payment_terms,
        credit_limit=supplier.credit_limit,

        upi_id=supplier.upi_id,

        bank_name=supplier.bank_name,
        account_number=supplier.account_number,
        ifsc_code=supplier.ifsc_code,

        notes=supplier.notes,

        is_active=True,
    )

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return new_supplier


# ----------------------------------------------------
# List Suppliers
# ----------------------------------------------------
def get_suppliers(
    db: Session,
    shop_id: int,
):

    return (
        db.query(Supplier)
        .filter(
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .order_by(Supplier.supplier_name)
        .all()
    )


# ----------------------------------------------------
# Get Supplier
# ----------------------------------------------------
def get_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
):

    return (
        db.query(Supplier)
        .filter(
            Supplier.id == supplier_id,
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .first()
    )


# ----------------------------------------------------
# Search Supplier
# ----------------------------------------------------
def search_supplier(
    db: Session,
    shop_id: int,
    keyword: str,
):

    keyword = f"%{keyword}%"

    return (
        db.query(Supplier)
        .filter(
            Supplier.shop_id == shop_id,
            Supplier.is_active == True,
        )
        .filter(
            (Supplier.supplier_name.ilike(keyword))
            | (Supplier.mobile.ilike(keyword))
            | (Supplier.supplier_code.ilike(keyword))
        )
        .all()
    )


# ----------------------------------------------------
# Update Supplier
# ----------------------------------------------------
def update_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
    supplier: SupplierUpdate,
):

    db_supplier = get_supplier(
        db,
        supplier_id,
        shop_id,
    )

    if not db_supplier:
        return None

    update_data = supplier.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(
            db_supplier,
            key,
            value,
        )

    db.commit()
    db.refresh(db_supplier)

    return db_supplier


# ----------------------------------------------------
# Soft Delete Supplier
# ----------------------------------------------------
def delete_supplier(
    db: Session,
    supplier_id: int,
    shop_id: int,
):

    supplier = get_supplier(
        db,
        supplier_id,
        shop_id,
    )

    if not supplier:
        return None

    supplier.is_active = False

    db.commit()

    return supplier