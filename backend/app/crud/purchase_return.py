from datetime import datetime

from sqlalchemy.orm import Session

from app.models.purchase_return import PurchaseReturn
from app.models.purchase_return_item import PurchaseReturnItem
from app.models.product_variant import ProductVariant


# ==========================================================
# Generate Return Number
# ==========================================================

def generate_return_number(shop_id: int):

    now = datetime.now()

    return f"PR-{shop_id}-{now.strftime('%Y%m%d%H%M%S')}"


# ==========================================================
# Create Purchase Return
# ==========================================================

def create_purchase_return(
    db: Session,
    shop_id: int,
    data,
):

    purchase_return = PurchaseReturn(

        shop_id=shop_id,

        purchase_id=data.purchase_id,

        supplier_id=data.supplier_id,

        return_number=generate_return_number(shop_id),

        reason=data.reason,

        total_amount=data.total_amount,

        status="Completed",

    )

    db.add(purchase_return)

    db.flush()

    # -------------------------------------------------------
    # Validate & Save Items
    # -------------------------------------------------------

    for item in data.items:

        variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.id == item.variant_id
            )
            .first()
        )

        if not variant:

            raise Exception(
                f"Variant {item.variant_id} not found."
            )

        if not variant.stock:

            raise Exception(
                f"No stock found for Variant {variant.id}"
            )

        # -------------------------------------
        # Quantity Validation
        # -------------------------------------

        if item.quantity != (
            item.k_quantity +
            item.r_quantity
        ):

            raise Exception(
                "Quantity must equal K Quantity + R Quantity"
            )

        # -------------------------------------
        # Check K Stock
        # -------------------------------------

        if item.k_quantity > variant.stock.k_stock:

            raise Exception(
                f"Not enough K Stock for SKU {variant.sku}"
            )

        # -------------------------------------
        # Check R Stock
        # -------------------------------------

        if item.r_quantity > variant.stock.r_stock:

            raise Exception(
                f"Not enough R Stock for SKU {variant.sku}"
            )

        # -------------------------------------
        # Reduce Stock
        # -------------------------------------

        variant.stock.k_stock -= item.k_quantity

        variant.stock.r_stock -= item.r_quantity

        # -------------------------------------
        # Save Item
        # -------------------------------------

        return_item = PurchaseReturnItem(

            purchase_return_id=purchase_return.id,

            variant_id=item.variant_id,

            quantity=item.quantity,

            k_quantity=item.k_quantity,

            r_quantity=item.r_quantity,

            cost_price=item.cost_price,

            total=item.total,

        )

        db.add(return_item)

    db.commit()

    db.refresh(purchase_return)

    return purchase_return


# ==========================================================
# Get All Purchase Returns
# ==========================================================

def get_all_purchase_returns(
    db: Session,
    shop_id: int,
):

    returns = (

        db.query(PurchaseReturn)

        .filter(
            PurchaseReturn.shop_id == shop_id
        )

        .order_by(
            PurchaseReturn.created_at.desc()
        )

        .all()

    )

    return returns


# ==========================================================
# Get Purchase Return Details
# ==========================================================

def get_purchase_return_by_id(
    db: Session,
    shop_id: int,
    return_id: int,
):

    purchase_return = (

        db.query(PurchaseReturn)

        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.id == return_id,
        )

        .first()

    )

    return purchase_return


# ==========================================================
# Search Purchase Return
# ==========================================================

def search_purchase_return(
    db: Session,
    shop_id: int,
    return_number: str,
):

    returns = (

        db.query(PurchaseReturn)

        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.return_number.ilike(
                f"%{return_number}%"
            ),
        )

        .all()

    )

    return returns


# ==========================================================
# Supplier Purchase Returns
# ==========================================================

def supplier_returns(
    db: Session,
    shop_id: int,
    supplier_id: int,
):

    returns = (

        db.query(PurchaseReturn)

        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.supplier_id == supplier_id,
        )

        .order_by(
            PurchaseReturn.created_at.desc()
        )

        .all()

    )

    return returns