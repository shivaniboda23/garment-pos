from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.purchase_return import (
    PurchaseReturn,
)
from app.models.purchase_return_item import (
    PurchaseReturnItem,
)
from app.models.product_variant import (
    ProductVariant,
)

from app.services.stock_movement import (
    record_stock_movement,
)


# ==========================================================
# Generate Return Number
# ==========================================================

def generate_return_number(
    shop_id: int,
):
    now = datetime.now()

    return (
        f"PR-{shop_id}-"
        f"{now.strftime('%Y%m%d%H%M%S%f')[:-3]}"
    )


# ==========================================================
# Create Purchase Return
# ==========================================================

def create_purchase_return(
    db: Session,
    shop_id: int,
    data,
):
    # -------------------------------------------------------
    # Validate Purchase
    # -------------------------------------------------------

    purchase = (
        db.query(Purchase)
        .filter(
            Purchase.id
            == data.purchase_id,

            Purchase.shop_id
            == shop_id,
        )
        .first()
    )

    if not purchase:
        raise ValueError(
            f"Purchase {data.purchase_id} "
            f"not found for this shop."
        )

    # -------------------------------------------------------
    # Validate Supplier
    # -------------------------------------------------------

    if (
        purchase.supplier_id
        != data.supplier_id
    ):
        raise ValueError(
            "Supplier does not match "
            "the selected purchase."
        )

    # -------------------------------------------------------
    # Validate Items
    # -------------------------------------------------------

    if not data.items:
        raise ValueError(
            "At least one purchase "
            "return item is required."
        )

    # -------------------------------------------------------
    # Generate Unique Return Number
    # -------------------------------------------------------

    return_number = generate_return_number(
        shop_id
    )

    while (
        db.query(PurchaseReturn)
        .filter(
            PurchaseReturn.return_number
            == return_number
        )
        .first()
    ):
        return_number = (
            generate_return_number(
                shop_id
            )
        )

    # -------------------------------------------------------
    # Create Return Header
    # -------------------------------------------------------

    purchase_return = PurchaseReturn(
        shop_id=shop_id,
        purchase_id=purchase.id,
        supplier_id=
            purchase.supplier_id,
        return_number=return_number,
        reason=data.reason,
        total_amount=data.total_amount,
        status="Completed",
    )

    db.add(
        purchase_return
    )

    db.flush()

    try:

        # ===================================================
        # PROCESS RETURN ITEMS
        # ===================================================

        for item in data.items:

            # ------------------------------------------------
            # Find Variant and Lock It
            # ------------------------------------------------

            variant = (
                db.query(
                    ProductVariant
                )
                .options(
                    joinedload(
                        ProductVariant.stock
                    ),
                    joinedload(
                        ProductVariant.product
                    ),
                )
                .filter(
                    ProductVariant.id
                    == item.variant_id,
                )
                .with_for_update()
                .first()
            )

            if not variant:
                raise ValueError(
                    f"Variant "
                    f"{item.variant_id} "
                    f"not found."
                )

            if not variant.product:
                raise ValueError(
                    f"Product for Variant "
                    f"{variant.id} "
                    f"not found."
                )

            if (
                variant.product.shop_id
                != shop_id
            ):
                raise ValueError(
                    "Variant does not "
                    "belong to this shop."
                )

            if not variant.stock:
                raise ValueError(
                    f"No stock record "
                    f"found for Variant "
                    f"{variant.id}."
                )

            stock = variant.stock

            # ------------------------------------------------
            # Validate Quantity
            # ------------------------------------------------

            if item.quantity <= 0:
                raise ValueError(
                    "Return quantity must "
                    "be greater than zero."
                )

            if item.k_quantity < 0:
                raise ValueError(
                    "K quantity cannot "
                    "be negative."
                )

            if item.r_quantity < 0:
                raise ValueError(
                    "R quantity cannot "
                    "be negative."
                )

            if item.quantity != (
                item.k_quantity
                + item.r_quantity
            ):
                raise ValueError(
                    "Quantity must equal "
                    "K Quantity + R Quantity."
                )

            # ------------------------------------------------
            # Find Original Purchase Items
            # ------------------------------------------------

            purchase_items = (
                db.query(
                    PurchaseItem
                )
                .filter(
                    PurchaseItem.purchase_id
                    == purchase.id,

                    PurchaseItem.variant_id
                    == item.variant_id,
                )
                .all()
            )

            if not purchase_items:
                raise ValueError(
                    f"Variant "
                    f"{item.variant_id} "
                    f"was not purchased "
                    f"in Purchase "
                    f"{purchase.id}."
                )

            # ------------------------------------------------
            # Calculate Purchased K/R
            # ------------------------------------------------

            purchased_k_quantity = 0
            purchased_r_quantity = 0

            for purchase_item in (
                purchase_items
            ):

                stock_type = (
                    purchase_item
                    .stock_type
                    or ""
                ).upper()

                if stock_type == "K":

                    purchased_k_quantity += (
                        purchase_item.quantity
                    )

                elif stock_type == "R":

                    purchased_r_quantity += (
                        purchase_item.quantity
                    )

                else:
                    raise ValueError(
                        f"Invalid stock type "
                        f"'{purchase_item.stock_type}' "
                        f"in Purchase Item "
                        f"{purchase_item.id}."
                    )

            # ------------------------------------------------
            # Previously Returned K
            # ------------------------------------------------

            previously_returned_k = (
                db.query(
                    func.coalesce(
                        func.sum(
                            PurchaseReturnItem
                            .k_quantity
                        ),
                        0,
                    )
                )
                .join(
                    PurchaseReturn,
                    PurchaseReturnItem
                    .purchase_return_id
                    == PurchaseReturn.id,
                )
                .filter(
                    PurchaseReturn.purchase_id
                    == purchase.id,

                    PurchaseReturnItem
                    .variant_id
                    == item.variant_id,

                    PurchaseReturn.status
                    == "Completed",
                )
                .scalar()
            )

            # ------------------------------------------------
            # Previously Returned R
            # ------------------------------------------------

            previously_returned_r = (
                db.query(
                    func.coalesce(
                        func.sum(
                            PurchaseReturnItem
                            .r_quantity
                        ),
                        0,
                    )
                )
                .join(
                    PurchaseReturn,
                    PurchaseReturnItem
                    .purchase_return_id
                    == PurchaseReturn.id,
                )
                .filter(
                    PurchaseReturn.purchase_id
                    == purchase.id,

                    PurchaseReturnItem
                    .variant_id
                    == item.variant_id,

                    PurchaseReturn.status
                    == "Completed",
                )
                .scalar()
            )

            previously_returned_k = int(
                previously_returned_k
                or 0
            )

            previously_returned_r = int(
                previously_returned_r
                or 0
            )

            # ------------------------------------------------
            # Remaining Returnable
            # ------------------------------------------------

            remaining_k_quantity = (
                purchased_k_quantity
                - previously_returned_k
            )

            remaining_r_quantity = (
                purchased_r_quantity
                - previously_returned_r
            )

            if remaining_k_quantity < 0:
                remaining_k_quantity = 0

            if remaining_r_quantity < 0:
                remaining_r_quantity = 0

            # ------------------------------------------------
            # Validate K Return
            # ------------------------------------------------

            if (
                item.k_quantity
                > remaining_k_quantity
            ):
                raise ValueError(
                    f"Cannot return "
                    f"{item.k_quantity} "
                    f"K units for Variant "
                    f"{item.variant_id}. "
                    f"Only "
                    f"{remaining_k_quantity} "
                    f"K units are still "
                    f"returnable."
                )

            # ------------------------------------------------
            # Validate R Return
            # ------------------------------------------------

            if (
                item.r_quantity
                > remaining_r_quantity
            ):
                raise ValueError(
                    f"Cannot return "
                    f"{item.r_quantity} "
                    f"R units for Variant "
                    f"{item.variant_id}. "
                    f"Only "
                    f"{remaining_r_quantity} "
                    f"R units are still "
                    f"returnable."
                )

            # ------------------------------------------------
            # Validate Current Stock K
            # ------------------------------------------------

            if (
                item.k_quantity
                > stock.k_stock
            ):
                raise ValueError(
                    f"Not enough K Stock "
                    f"for SKU "
                    f"{variant.sku}. "
                    f"Available: "
                    f"{stock.k_stock}, "
                    f"Requested return: "
                    f"{item.k_quantity}."
                )

            # ------------------------------------------------
            # Validate Current Stock R
            # ------------------------------------------------

            if (
                item.r_quantity
                > stock.r_stock
            ):
                raise ValueError(
                    f"Not enough R Stock "
                    f"for SKU "
                    f"{variant.sku}. "
                    f"Available: "
                    f"{stock.r_stock}, "
                    f"Requested return: "
                    f"{item.r_quantity}."
                )

            # =================================================
            # REMOVE K STOCK
            # =================================================

            if item.k_quantity > 0:

                k_before = int(
                    stock.k_stock
                    or 0
                )

                stock.k_stock -= (
                    item.k_quantity
                )

                k_after = int(
                    stock.k_stock
                    or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=shop_id,
                    variant_id=variant.id,
                    movement_type=
                        "PURCHASE_RETURN",
                    stock_type="K",
                    quantity=(
                        -item.k_quantity
                    ),
                    quantity_before=
                        k_before,
                    quantity_after=
                        k_after,
                    reference_type=
                        "PURCHASE_RETURN",
                    reference_id=
                        purchase_return.id,
                    reference_number=
                        purchase_return
                        .return_number,
                    reason=
                        purchase_return.reason,
                )

            # =================================================
            # REMOVE R STOCK
            # =================================================

            if item.r_quantity > 0:

                r_before = int(
                    stock.r_stock
                    or 0
                )

                stock.r_stock -= (
                    item.r_quantity
                )

                r_after = int(
                    stock.r_stock
                    or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=shop_id,
                    variant_id=variant.id,
                    movement_type=
                        "PURCHASE_RETURN",
                    stock_type="R",
                    quantity=(
                        -item.r_quantity
                    ),
                    quantity_before=
                        r_before,
                    quantity_after=
                        r_after,
                    reference_type=
                        "PURCHASE_RETURN",
                    reference_id=
                        purchase_return.id,
                    reference_number=
                        purchase_return
                        .return_number,
                    reason=
                        purchase_return.reason,
                )

            # ------------------------------------------------
            # Save Return Item
            # ------------------------------------------------

            return_item = (
                PurchaseReturnItem(
                    purchase_return_id=
                        purchase_return.id,
                    variant_id=
                        item.variant_id,
                    quantity=
                        item.quantity,
                    k_quantity=
                        item.k_quantity,
                    r_quantity=
                        item.r_quantity,
                    cost_price=
                        item.cost_price,
                    total=
                        item.total,
                )
            )

            db.add(
                return_item
            )

        # ---------------------------------------------------
        # Commit
        # ---------------------------------------------------

        db.commit()

        db.refresh(
            purchase_return
        )

        return purchase_return

    except Exception:
        db.rollback()
        raise


# ==========================================================
# Get All Purchase Returns
# ==========================================================

def get_all_purchase_returns(
    db: Session,
    shop_id: int,
):
    return (
        db.query(
            PurchaseReturn
        )
        .options(
            joinedload(
                PurchaseReturn.items
            )
            .joinedload(
                PurchaseReturnItem.variant
            )
        )
        .filter(
            PurchaseReturn.shop_id
            == shop_id
        )
        .order_by(
            PurchaseReturn.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Get Purchase Return Details
# ==========================================================

def get_purchase_return_by_id(
    db: Session,
    shop_id: int,
    return_id: int,
):
    return (
        db.query(
            PurchaseReturn
        )
        .options(
            joinedload(
                PurchaseReturn.items
            )
            .joinedload(
                PurchaseReturnItem.variant
            )
        )
        .filter(
            PurchaseReturn.shop_id
            == shop_id,

            PurchaseReturn.id
            == return_id,
        )
        .first()
    )


# ==========================================================
# Search Purchase Return
# ==========================================================

def search_purchase_return(
    db: Session,
    shop_id: int,
    return_number: str,
):
    return (
        db.query(
            PurchaseReturn
        )
        .options(
            joinedload(
                PurchaseReturn.items
            )
            .joinedload(
                PurchaseReturnItem.variant
            )
        )
        .filter(
            PurchaseReturn.shop_id
            == shop_id,

            PurchaseReturn.return_number
            .ilike(
                f"%{return_number}%"
            ),
        )
        .order_by(
            PurchaseReturn.created_at.desc()
        )
        .all()
    )


# ==========================================================
# Supplier Purchase Returns
# ==========================================================

def supplier_returns(
    db: Session,
    shop_id: int,
    supplier_id: int,
):
    return (
        db.query(
            PurchaseReturn
        )
        .options(
            joinedload(
                PurchaseReturn.items
            )
            .joinedload(
                PurchaseReturnItem.variant
            )
        )
        .filter(
            PurchaseReturn.shop_id
            == shop_id,

            PurchaseReturn.supplier_id
            == supplier_id,
        )
        .order_by(
            PurchaseReturn.created_at.desc()
        )
        .all()
    )