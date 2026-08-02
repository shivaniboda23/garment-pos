from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db


from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)

from app.crud.supplier import (
    create_supplier,
    get_suppliers,
    get_supplier,
    update_supplier,
    delete_supplier,
    search_supplier,
)

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

# Temporary
from app.core.config import TEMP_SHOP_ID


@router.post(
    "/",
    response_model=SupplierResponse,
)
def create_supplier_api(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
):
    return create_supplier(
        db,
        TEMP_SHOP_ID,
        supplier,
    )


@router.get(
    "/",
    response_model=List[SupplierResponse],
)
def list_suppliers(
    db: Session = Depends(get_db),
):
    return get_suppliers(
        db,
        TEMP_SHOP_ID,
    )


@router.get(
    "/search",
    response_model=List[SupplierResponse],
)
def search_supplier_api(
    keyword: str,
    db: Session = Depends(get_db),
):
    return search_supplier(
        db,
        TEMP_SHOP_ID,
        keyword,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def get_supplier_api(
    supplier_id: int,
    db: Session = Depends(get_db),
):

    supplier = get_supplier(
        db,
        supplier_id,
        TEMP_SHOP_ID,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def update_supplier_api(
    supplier_id: int,
    supplier: SupplierUpdate,
    db: Session = Depends(get_db),
):

    updated = update_supplier(
        db,
        supplier_id,
        TEMP_SHOP_ID,
        supplier,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return updated


@router.delete("/{supplier_id}")
def delete_supplier_api(
    supplier_id: int,
    db: Session = Depends(get_db),
):

    supplier = delete_supplier(
        db,
        supplier_id,
        TEMP_SHOP_ID,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return {
        "message": "Supplier deleted successfully"
    }