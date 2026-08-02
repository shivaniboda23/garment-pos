from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.sale_return import SaleReturn
from app.models.sale_return_item import SaleReturnItem
from app.models.product_variant import ProductVariant
from app.models.stock import Stock

# ==========================================================
# Generate Return Number
# ==========================================================

def generate_return_number(shop_id: int):

    now = datetime.now()

    return f"SR-{shop_id}-{now.strftime('%Y%m%d%H%M%S')}"


# ==========================================================
# CREATE SALE RETURN
# ==========================================================

def create_sale_return(
    db: Session,
    shop_id: int,
    data,
):

    sale = (
        db.query(Sale)
        .filter(
            Sale.id == data.sale_id,
            Sale.shop_id == shop_id,
        )
        .first()
    )

    if not sale:
        raise Exception("Sale not found")

    sale_return = SaleReturn(

        shop_id=shop_id,

        sale_id=data.sale_id,

        customer_id=data.customer_id,

        return_number=generate_return_number(shop_id),

        reason=data.reason,

        refund_amount=data.refund_amount,

        status="Completed",

    )

    db.add(sale_return)

    db.flush()

    for item in data.items:

        sale_item = (
            db.query(SaleItem)
            .filter(
                SaleItem.sale_id == data.sale_id,
                SaleItem.variant_id == item.variant_id,
            )
            .first()
        )

        if not sale_item:

            raise Exception(
                f"Variant {item.variant_id} not found in Sale."
            )

        if item.quantity > sale_item.quantity:

            raise Exception(
                "Return quantity exceeds sold quantity."
            )

        variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.id == item.variant_id,
            )
            .first()
        )

        if not variant:

            raise Exception("Variant not found.")

        if not variant.stock:

            raise Exception("Stock record not found.")

        # Increase Stock: A sale return increases the available stock ('k_stock').
        variant.stock.k_stock += item.quantity

        refund = Decimal(sale_item.unit_price) * item.quantity

        return_item = SaleReturnItem(

            sale_return_id=sale_return.id,

            variant_id=item.variant_id,

            quantity=item.quantity,

            unit_price=sale_item.unit_price,

            refund_amount=refund,

        )

        db.add(return_item)

    db.commit()

    db.refresh(sale_return)

    return sale_return


# ==========================================================
# GET ALL SALE RETURNS
# ==========================================================

def get_all_sale_returns(
    db: Session,
    shop_id: int,
):

    returns = (

        db.query(SaleReturn)

        .options(

            joinedload(SaleReturn.customer),

            joinedload(SaleReturn.sale),

        )

        .filter(
            SaleReturn.shop_id == shop_id,
        )

        .order_by(
            SaleReturn.created_at.desc()
        )

        .all()

    )

    return returns


# ==========================================================
# GET RETURN DETAILS
# ==========================================================

def get_sale_return_by_id(
    db: Session,
    shop_id: int,
    return_id: int,
):

    sale_return = (

        db.query(SaleReturn)

        .options(

            joinedload(SaleReturn.customer),

            joinedload(SaleReturn.sale),

            joinedload(SaleReturn.items)
            .joinedload(
                SaleReturnItem.variant
            ),

        )

        .filter(

            SaleReturn.id == return_id,

            SaleReturn.shop_id == shop_id,

        )

        .first()

    )

    return sale_return