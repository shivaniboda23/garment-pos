from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.services.stock_movement import (
    record_stock_movement,
)


# ==========================================================
# CREATE STOCK
# ==========================================================

def create_stock(
    db: Session,
    shop_id: int,
    data,
):
    variant = (
        db.query(ProductVariant)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .filter(
            ProductVariant.id == data.variant_id,
            Product.shop_id == shop_id,
        )
        .first()
    )

    if not variant:
        return None

    stock = (
        db.query(Stock)
        .filter(
            Stock.variant_id == data.variant_id
        )
        .first()
    )

    if stock:
        stock.k_stock += data.k_stock
        stock.r_stock += data.r_stock

        stock.minimum_stock = (
            data.minimum_stock
        )

        stock.k_minimum_stock = (
            data.k_minimum_stock
        )

        stock.r_minimum_stock = (
            data.r_minimum_stock
        )

        stock.maximum_stock = (
            data.maximum_stock
        )

    else:
        stock = Stock(
            variant_id=data.variant_id,
            k_stock=data.k_stock,
            r_stock=data.r_stock,
            minimum_stock=data.minimum_stock,
            k_minimum_stock=data.k_minimum_stock,
            r_minimum_stock=data.r_minimum_stock,
            maximum_stock=data.maximum_stock,
        )

        db.add(stock)

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# GET ALL STOCK
# ==========================================================

def get_all_stock(
    db: Session,
    shop_id: int,
):
    return (
        db.query(Stock)
        .join(
            ProductVariant,
            ProductVariant.id == Stock.variant_id,
        )
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .filter(
            Product.shop_id == shop_id,
        )
        .all()
    )


# ==========================================================
# GET STOCK BY VARIANT
# ==========================================================

def get_stock_by_variant(
    db: Session,
    variant_id: int,
):
    return (
        db.query(Stock)
        .filter(
            Stock.variant_id == variant_id
        )
        .first()
    )


# ==========================================================
# UPDATE STOCK
# ==========================================================

def update_stock(
    db: Session,
    shop_id: int,
    variant_id: int,
    k_stock: int,
    r_stock: int,
    minimum_stock: int,
    k_minimum_stock: int,
    r_minimum_stock: int,
    maximum_stock: int,
):
    stock = (
        db.query(Stock)
        .join(
            ProductVariant,
            ProductVariant.id == Stock.variant_id,
        )
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .filter(
            Stock.variant_id == variant_id,
            Product.shop_id == shop_id,
        )
        .first()
    )

    if not stock:
        return None

    stock.k_stock = k_stock
    stock.r_stock = r_stock

    stock.k_minimum_stock = (
        k_minimum_stock
    )

    stock.r_minimum_stock = (
        r_minimum_stock
    )

    stock.minimum_stock = (
        minimum_stock
    )

    stock.maximum_stock = (
        maximum_stock
    )

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# PHYSICAL STOCK ADJUSTMENT
# ==========================================================

def adjust_physical_stock(
    db: Session,
    shop_id: int,
    data,
):
    try:
        # Lock only the variant base row. The inner join is
        # used solely to enforce the authenticated shop.
        variant = (
            db.query(ProductVariant)
            .join(
                Product,
                Product.id
                == ProductVariant.product_id,
            )
            .filter(
                ProductVariant.id
                == data.variant_id,

                Product.shop_id
                == shop_id,
            )
            .with_for_update(
                of=ProductVariant
            )
            .first()
        )

        if not variant:
            raise HTTPException(
                status_code=404,
                detail="Variant not found.",
            )

        # Stock is the row whose quantities are changed, so
        # lock it directly before reading either bucket.
        stock = (
            db.query(Stock)
            .filter(
                Stock.variant_id
                == variant.id,
            )
            .with_for_update(
                of=Stock
            )
            .first()
        )

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="Stock record not found.",
            )

        if data.stock_type == "K":
            before = int(stock.k_stock or 0)
        else:
            before = int(stock.r_stock or 0)

        after = int(data.counted_quantity)
        quantity_change = after - before

        if after < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Physical quantity cannot "
                    "be negative."
                ),
            )

        if quantity_change == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No stock adjustment "
                    "required."
                ),
            )

        if data.stock_type == "K":
            stock.k_stock = after
        else:
            stock.r_stock = after

        movement = record_stock_movement(
            db=db,
            shop_id=shop_id,
            variant_id=variant.id,
            movement_type="STOCK_ADJUSTMENT",
            stock_type=data.stock_type,
            quantity=quantity_change,
            quantity_before=before,
            quantity_after=after,
            reference_type="PHYSICAL_COUNT",
            reference_id=None,
            reference_number=None,
            reason=data.reason,
            notes=data.notes,
        )

        db.flush()
        movement_id = movement.id
        reference_number = (
            movement.reference_number
        )
        db.commit()

        return {
            "success": True,
            "variant_id": variant.id,
            "stock_type": data.stock_type,
            "quantity_before": before,
            "quantity_after": after,
            "quantity_change": quantity_change,
            "reason": data.reason,
            "movement_id": movement_id,
            "reference_number": reference_number,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Stock adjustment could not "
                "be completed."
            ),
        ) from None


# ==========================================================
# INCREASE K STOCK
# ==========================================================

def add_k_stock(
    db: Session,
    variant_id: int,
    quantity: int,
):
    stock = get_stock_by_variant(
        db,
        variant_id,
    )

    if not stock:
        return None

    stock.k_stock += quantity

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# INCREASE R STOCK
# ==========================================================

def add_r_stock(
    db: Session,
    variant_id: int,
    quantity: int,
):
    stock = get_stock_by_variant(
        db,
        variant_id,
    )

    if not stock:
        return None

    stock.r_stock += quantity

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# TOTAL STOCK
# ==========================================================

def get_total_stock(
    db: Session,
    variant_id: int,
):
    stock = get_stock_by_variant(
        db,
        variant_id,
    )

    if not stock:
        return 0

    return (
        stock.k_stock
        + stock.r_stock
    )
