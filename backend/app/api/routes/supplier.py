from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user


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

@router.post(
    "/",
    response_model=SupplierResponse,
)
def create_supplier_api(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_supplier(
        db=db,
        shop_id=current_user.shop_id,
        supplier=supplier,
    )


@router.get(
    "/",
    response_model=List[SupplierResponse],
)
def list_suppliers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_suppliers(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/search",
    response_model=List[SupplierResponse],
)
def search_supplier_api(
    keyword: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return search_supplier(
        db=db,
        shop_id=current_user.shop_id,
        keyword=keyword,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def get_supplier_api(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    supplier = get_supplier(
        db=db,
        supplier_id=supplier_id,
        shop_id=current_user.shop_id,
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
    current_user=Depends(get_current_user),
):

    updated = update_supplier(
        db=db,
        supplier_id=supplier_id,
        shop_id=current_user.shop_id,
        supplier=supplier,
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
    current_user=Depends(get_current_user),
):

    supplier = delete_supplier(
        db=db,
        supplier_id=supplier_id,
        shop_id=current_user.shop_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return {
        "message": "Supplier deleted successfully"
    }
