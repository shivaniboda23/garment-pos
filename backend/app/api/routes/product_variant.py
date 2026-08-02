from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantResponse,
)

from app.crud.product_variant import (
    create_variant,
    get_variants,
    get_variant,
    update_variant,
    delete_variant,
)

router = APIRouter(
    prefix="/variants",
    tags=["Product Variants"],
)


@router.post(
    "",
    response_model=ProductVariantResponse,
)
def add_variant(
    request: ProductVariantCreate,
    db: Session = Depends(get_db),
):

    variant = create_variant(
        db,
        request,
    )

    if variant is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return variant


@router.get(
    "/product/{product_id}",
    response_model=list[ProductVariantResponse],
)
def list_variants(
    product_id: int,
    db: Session = Depends(get_db),
):

    return get_variants(
        db,
        product_id,
    )


@router.get(
    "/{variant_id}",
    response_model=ProductVariantResponse,
)
def get_single_variant(
    variant_id: int,
    db: Session = Depends(get_db),
):

    variant = get_variant(
        db,
        variant_id,
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return variant


@router.put(
    "/{variant_id}",
    response_model=ProductVariantResponse,
)
def edit_variant(
    variant_id: int,
    request: ProductVariantCreate,
    db: Session = Depends(get_db),
):

    variant = update_variant(
        db,
        variant_id,
        request,
    )

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Variant or Product not found",
        )

    return variant


@router.delete(
    "/{variant_id}",
)
def remove_variant(
    variant_id: int,
    db: Session = Depends(get_db),
):

    success = delete_variant(
        db,
        variant_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Variant not found",
        )

    return {
        "message": "Variant deleted successfully"
    }