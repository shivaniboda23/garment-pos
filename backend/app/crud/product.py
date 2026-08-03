import random

from sqlalchemy import or_
from sqlalchemy.orm import Session


from app.models.product import Product



# --------------------------------------------------
# Create Product
# --------------------------------------------------
def create_product(db: Session, product, shop_id: int):

    # Generate unique product code
    product_code = f"PRD{random.randint(100000, 999999)}"

    while (
        db.query(Product)
        .filter(Product.product_code == product_code)
        .first()
    ):
        product_code = f"PRD{random.randint(100000, 999999)}"

    new_product = Product(
        shop_id=shop_id,
        category_id=product.category_id,
        brand_id=product.brand_id,
        product_name=product.product_name,
        product_code=product_code,
        description=product.description,
        hsn_code=product.hsn_code,
        gst_percentage=product.gst_percentage,
        cost_price=product.cost_price,
        selling_price=product.selling_price,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# --------------------------------------------------
# List Products
# --------------------------------------------------
def get_products(db: Session, shop_id: int):

    return (
        db.query(Product)
        .filter(Product.shop_id == shop_id)
        .order_by(Product.product_name)
        .all()
    )


# --------------------------------------------------
# Get Single Product
# --------------------------------------------------
def get_product(db: Session, product_id: int, shop_id: int):

    return (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.shop_id == shop_id,
        )
        .first()
    )


# --------------------------------------------------
# Update Product
# --------------------------------------------------
def update_product(db: Session, product_id: int, data, shop_id: int):

    product = get_product(
        db,
        product_id,
        shop_id,
    )

    if not product:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


# --------------------------------------------------
# Delete Product
# --------------------------------------------------
def delete_product(db: Session, product_id: int, shop_id: int):

    product = get_product(
        db,
        product_id,
        shop_id,
    )

    if not product:
        return False

    db.delete(product)
    db.commit()

    return True


# --------------------------------------------------
# Search Products
# --------------------------------------------------
def search_products(db: Session, keyword: str, shop_id: int):
    keyword = keyword.strip()
    search_term = f"%{keyword}%"

    return (
        db.query(Product)
        .filter(
            Product.shop_id == shop_id,
            or_(
                Product.product_name.ilike(search_term),
                Product.product_code.ilike(search_term),
            ),
        )
        .order_by(Product.product_name)
        .limit(20)
        .all()
    )