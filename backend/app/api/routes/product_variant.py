from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantResponse,
)

from app.crud.product_variant import (
    create_variant,
    get_all_variants,
    get_variants,
    get_variant,
    update_variant,
    delete_variant,
)


router = APIRouter(
    prefix="/variants",
    tags=["Product Variants"],
)


# ==========================================================
# LIST ALL ACTIVE VARIANTS FOR CURRENT SHOP
# ==========================================================

@router.get(
    "",
)
def list_all_variants(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variants = get_all_variants(
        db=db,
        shop_id=current_user.shop_id,
    )

    return [
        {
            "id": variant.id,
            "product_id": variant.product_id,
            "product_name": (
                variant.product.product_name
                if variant.product
                else None
            ),
            "product_code": (
                variant.product.product_code
                if variant.product
                else None
            ),
            "sku": variant.sku,
            "barcode": variant.barcode,
            "size": variant.size,
            "color": variant.color,
            "reorder_level": variant.reorder_level,
            "cost_price": variant.cost_price,
            "selling_price": variant.selling_price,
            "gst_percentage": (
                variant.product.gst_percentage
                if variant.product
                else 0
            ),
            "is_active": variant.is_active,
            "stock": {
                "k_stock": (
                    variant.stock.k_stock
                    if variant.stock
                    else 0
                ),
                "r_stock": (
                    variant.stock.r_stock
                    if variant.stock
                    else 0
                ),
                "quantity": (
                    (
                        variant.stock.k_stock
                        + variant.stock.r_stock
                    )
                    if variant.stock
                    else 0
                ),
            },
        }
        for variant in variants
    ]


# ==========================================================
# CREATE VARIANT
# ==========================================================

@router.post(
    "",
    response_model=ProductVariantResponse,
)
def add_variant(
    request: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variant = create_variant(
        db=db,
        data=request,
        shop_id=current_user.shop_id,
    )

    if variant is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return variant


# ==========================================================
# LIST VARIANTS FOR PRODUCT
# ==========================================================

@router.get(
    "/product/{product_id}",
    response_model=list[ProductVariantResponse],
)
def list_variants(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_variants(
        db=db,
        product_id=product_id,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# GET SINGLE VARIANT
# IMPORTANT: keep after /product/{product_id}
# ==========================================================

@router.get(
    "/{variant_id}",
    response_model=ProductVariantResponse,
)
def get_single_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variant = get_variant(
        db=db,
        variant_id=variant_id,
        shop_id=current_user.shop_id,
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return variant


# ==========================================================
# UPDATE VARIANT
# ==========================================================

@router.put(
    "/{variant_id}",
    response_model=ProductVariantResponse,
)
def edit_variant(
    variant_id: int,
    request: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    variant = update_variant(
        db=db,
        variant_id=variant_id,
        data=request,
        shop_id=current_user.shop_id,
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Variant or Product not found",
        )

    return variant


# ==========================================================
# DELETE VARIANT
# ==========================================================

@router.delete(
    "/{variant_id}",
)
def remove_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = delete_variant(
        db=db,
        variant_id=variant_id,
        shop_id=current_user.shop_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return {
        "message": "Variant deleted successfully"
    }