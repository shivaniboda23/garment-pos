from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.product import ProductCreate

from app.crud.product import (
    create_product,
    get_products,
    get_product,
    update_product,
    delete_product,
    search_products,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# ---------------------------------------------------
# Create Product
# ---------------------------------------------------
@router.post("")
def add_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_product(
        db=db,
        product=request,
        shop_id=current_user.shop_id,
    )


# ---------------------------------------------------
# List Products
# ---------------------------------------------------
@router.get("")
def list_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_products(
        db=db,
        shop_id=current_user.shop_id,
    )


# ---------------------------------------------------
# Search Products
# IMPORTANT: Keep this ABOVE /{product_id}
# ---------------------------------------------------
@router.get("/search")
def search(
    q: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return search_products(
        db=db,
        keyword=q,
        shop_id=current_user.shop_id,
    )


# ---------------------------------------------------
# Product Details
# ---------------------------------------------------
@router.get("/{product_id}")
def get_single_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = get_product(
        db=db,
        product_id=product_id,
        shop_id=current_user.shop_id,
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# ---------------------------------------------------
# Update Product
# ---------------------------------------------------
@router.put("/{product_id}")
def edit_product(
    product_id: int,
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    product = update_product(
        db=db,
        product_id=product_id,
        data=request,
        shop_id=current_user.shop_id,
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


# ---------------------------------------------------
# Delete Product
# ---------------------------------------------------
@router.delete("/{product_id}")
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = delete_product(
        db=db,
        product_id=product_id,
        shop_id=current_user.shop_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return {
        "message": "Product deleted successfully"
    }