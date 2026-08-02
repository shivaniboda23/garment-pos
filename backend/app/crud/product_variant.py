from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.stock import Stock


# --------------------------------------------------
# Create Variant
# --------------------------------------------------

def create_variant(
    db: Session,
    data,
):

    product = (
        db.query(Product)
        .filter(Product.id == data.product_id)
        .first()
    )

    if not product:
        return None

    variant = ProductVariant(
        product_id=data.product_id,
        size=data.size,
        color=data.color,
        sku=data.sku,
        barcode=data.barcode,
        reorder_level=data.reorder_level,
        cost_price=data.cost_price,
        selling_price=data.selling_price,
        is_active=True,
    )

    db.add(variant)

    db.flush()

    stock = Stock(
        variant_id=variant.id,
        k_stock=0,
        r_stock=0,
        minimum_stock=data.reorder_level,
        maximum_stock=0,
    )

    db.add(stock)

    db.commit()

    db.refresh(variant)

    return variant


# --------------------------------------------------
# Get Variants
# --------------------------------------------------

def get_variants(
    db: Session,
    product_id: int,
):

    return (
        db.query(ProductVariant)
        .filter(ProductVariant.product_id == product_id)
        .all()
    )


# --------------------------------------------------
# Get Variant
# --------------------------------------------------

def get_variant(
    db: Session,
    variant_id: int,
):

    return (
        db.query(ProductVariant)
        .filter(ProductVariant.id == variant_id)
        .first()
    )


# --------------------------------------------------
# Update Variant
# --------------------------------------------------

def update_variant(
    db: Session,
    variant_id: int,
    data,
):

    variant = get_variant(
        db,
        variant_id,
    )

    if not variant:
        return None

    product = (
        db.query(Product)
        .filter(Product.id == data.product_id)
        .first()
    )

    if not product:
        return None

    variant.product_id = data.product_id
    variant.size = data.size
    variant.color = data.color
    variant.reorder_level = data.reorder_level
    variant.cost_price = data.cost_price
    variant.selling_price = data.selling_price

    if variant.stock:

        # Preserve existing stock values
        variant.stock.minimum_stock = data.reorder_level

    else:

        stock = Stock(
            variant_id=variant.id,
            k_stock=0,
            r_stock=0,
            minimum_stock=data.reorder_level,
            maximum_stock=0,
        )

        db.add(stock)

    db.commit()

    db.refresh(variant)

    return variant


# --------------------------------------------------
# Delete Variant
# --------------------------------------------------

def delete_variant(
    db: Session,
    variant_id: int,
):

    variant = get_variant(
        db,
        variant_id,
    )

    if not variant:
        return False

    db.delete(variant)

    db.commit()

    return True