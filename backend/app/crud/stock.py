from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.product_variant import ProductVariant


# ==========================================================
# Create Stock
# ==========================================================

def create_stock(db: Session, data):

    variant = (
        db.query(ProductVariant)
        .filter(ProductVariant.id == data.variant_id)
        .first()
    )

    if not variant:
        return None

    stock = (
        db.query(Stock)
        .filter(Stock.variant_id == data.variant_id)
        .first()
    )

    if stock:

        stock.k_stock += data.k_stock
        stock.r_stock += data.r_stock

        if hasattr(data, "minimum_stock"):
            stock.minimum_stock = data.minimum_stock

        if hasattr(data, "maximum_stock"):
            stock.maximum_stock = data.maximum_stock

    else:

        stock = Stock(
            variant_id=data.variant_id,
            k_stock=data.k_stock,
            r_stock=data.r_stock,
            minimum_stock=getattr(data, "minimum_stock", 0),
            maximum_stock=getattr(data, "maximum_stock", 0),
        )

        db.add(stock)

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# Get All Stock
# ==========================================================

def get_all_stock(db: Session):

    return (
        db.query(Stock)
        .all()
    )


# ==========================================================
# Get Single Stock
# ==========================================================

def get_stock_by_variant(
    db: Session,
    variant_id: int,
):

    return (
        db.query(Stock)
        .filter(Stock.variant_id == variant_id)
        .first()
    )


# ==========================================================
# Update Stock
# ==========================================================

def update_stock(
    db: Session,
    variant_id: int,
    k_stock: int,
    r_stock: int,
    minimum_stock: int = 0,
    maximum_stock: int = 0,
):

    stock = (
        db.query(Stock)
        .filter(Stock.variant_id == variant_id)
        .first()
    )

    if not stock:
        return None

    stock.k_stock = k_stock
    stock.r_stock = r_stock
    stock.minimum_stock = minimum_stock
    stock.maximum_stock = maximum_stock

    db.commit()
    db.refresh(stock)

    return stock


# ==========================================================
# Increase K Stock
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
# Increase R Stock
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
# Total Stock
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

    return stock.k_stock + stock.r_stock