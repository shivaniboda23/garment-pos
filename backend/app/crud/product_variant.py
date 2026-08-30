from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.stock import Stock


# ==========================================================
# CREATE VARIANT
# ==========================================================

def create_variant(
    db: Session,
    data,
    shop_id: int,
):
    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.shop_id == shop_id,
        )
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


# ==========================================================
# GET ALL VARIANTS FOR SHOP
# ==========================================================

def get_all_variants(
    db: Session,
    shop_id: int,
):
    return (
        db.query(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .options(
            joinedload(
                ProductVariant.product
            ),
            joinedload(
                ProductVariant.stock
            ),
        )
        .filter(
            Product.shop_id == shop_id,
            ProductVariant.is_active == True,
        )
        .order_by(
            Product.product_name,
            ProductVariant.size,
            ProductVariant.color,
        )
        .all()
    )


# ==========================================================
# GET VARIANTS FOR PRODUCT
# ==========================================================

def get_variants(
    db: Session,
    product_id: int,
    shop_id: int,
):
    return (
        db.query(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .options(
            joinedload(
                ProductVariant.product
            ),
            joinedload(
                ProductVariant.stock
            ),
        )
        .filter(
            ProductVariant.product_id == product_id,
            Product.shop_id == shop_id,
        )
        .order_by(
            ProductVariant.size,
            ProductVariant.color,
        )
        .all()
    )


# ==========================================================
# GET VARIANT
# ==========================================================

def get_variant(
    db: Session,
    variant_id: int,
    shop_id: int,
):
    return (
        db.query(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .options(
            joinedload(
                ProductVariant.product
            ),
            joinedload(
                ProductVariant.stock
            ),
        )
        .filter(
            ProductVariant.id == variant_id,
            Product.shop_id == shop_id,
        )
        .first()
    )


# ==========================================================
# UPDATE VARIANT
# ==========================================================

def update_variant(
    db: Session,
    variant_id: int,
    data,
    shop_id: int,
):
    variant = get_variant(
        db=db,
        variant_id=variant_id,
        shop_id=shop_id,
    )

    if not variant:
        return None

    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.shop_id == shop_id,
        )
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
        variant.stock.minimum_stock = (
            data.reorder_level
        )
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


# ==========================================================
# DELETE VARIANT
# ==========================================================

def delete_variant(
    db: Session,
    variant_id: int,
    shop_id: int,
):
    variant = get_variant(
        db=db,
        variant_id=variant_id,
        shop_id=shop_id,
    )

    if not variant:
        return False

    db.delete(variant)
    db.commit()

    return True