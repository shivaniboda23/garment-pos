from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.sale_return import SaleReturn
from app.models.sale_return_item import (
    SaleReturnItem,
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
        f"SR-{shop_id}-"
        f"{now.strftime('%Y%m%d%H%M%S%f')[:-3]}"
    )


# ==========================================================
# CREATE SALE RETURN
# ==========================================================

def create_sale_return(
    db: Session,
    shop_id: int,
    data,
):

    # ------------------------------------------------------
    # Validate Sale
    # ------------------------------------------------------

    sale = (
        db.query(Sale)
        .filter(
            Sale.id == data.sale_id,
            Sale.shop_id == shop_id,
        )
        .first()
    )

    if not sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found.",
        )

    # ------------------------------------------------------
    # Validate Customer
    # ------------------------------------------------------

    if (
        sale.customer_id
        != data.customer_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Customer does not match "
                "the selected sale."
            ),
        )

    # ------------------------------------------------------
    # Validate Items
    # ------------------------------------------------------

    if not data.items:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least one return "
                "item is required."
            ),
        )

    try:

        # --------------------------------------------------
        # Generate Return Number
        # --------------------------------------------------

        return_number = (
            generate_return_number(
                shop_id
            )
        )

        while (
            db.query(SaleReturn)
            .filter(
                SaleReturn.return_number
                == return_number
            )
            .first()
        ):
            return_number = (
                generate_return_number(
                    shop_id
                )
            )

        # --------------------------------------------------
        # Create Return Header
        # --------------------------------------------------

        sale_return = SaleReturn(
            shop_id=shop_id,
            sale_id=sale.id,
            customer_id=sale.customer_id,
            return_number=return_number,
            reason=data.reason,
            refund_amount=
                data.refund_amount,
            status="Completed",
        )

        db.add(
            sale_return
        )

        db.flush()

        # ==================================================
        # PROCESS EACH ITEM
        # ==================================================

        for item in data.items:

            # ----------------------------------------------
            # Lock SaleItem
            # ----------------------------------------------

            sale_item = (
                db.query(SaleItem)
                .filter(
                    SaleItem.sale_id
                    == sale.id,

                    SaleItem.variant_id
                    == item.variant_id,
                )
                .with_for_update()
                .first()
            )

            if not sale_item:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Variant "
                        f"{item.variant_id} "
                        f"not found in Sale "
                        f"{sale.id}."
                    ),
                )

            # ----------------------------------------------
            # Find Variant and Lock It
            # ----------------------------------------------

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
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Variant "
                        f"{item.variant_id} "
                        f"not found."
                    ),
                )

            if not variant.product:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Product not found "
                        "for variant."
                    ),
                )

            if (
                variant.product.shop_id
                != shop_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Variant does not "
                        "belong to this shop."
                    ),
                )

            if not variant.stock:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Stock record not "
                        "found for variant."
                    ),
                )

            stock = variant.stock

            # ----------------------------------------------
            # Validate Return Quantities
            # ----------------------------------------------

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Return quantity "
                        "must be greater "
                        "than zero."
                    ),
                )

            if item.k_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "K quantity cannot "
                        "be negative."
                    ),
                )

            if item.r_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "R quantity cannot "
                        "be negative."
                    ),
                )

            if item.quantity != (
                item.k_quantity
                + item.r_quantity
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Quantity must equal "
                        "K Quantity + "
                        "R Quantity."
                    ),
                )

            # ----------------------------------------------
            # Previously Returned K
            # ----------------------------------------------

            previous_k = (
                db.query(
                    func.coalesce(
                        func.sum(
                            SaleReturnItem
                            .k_quantity
                        ),
                        0,
                    )
                )
                .join(
                    SaleReturn,
                    SaleReturnItem
                    .sale_return_id
                    == SaleReturn.id,
                )
                .filter(
                    SaleReturn.sale_id
                    == sale.id,

                    SaleReturnItem.variant_id
                    == item.variant_id,

                    SaleReturn.status
                    == "Completed",
                )
                .scalar()
            )

            # ----------------------------------------------
            # Previously Returned R
            # ----------------------------------------------

            previous_r = (
                db.query(
                    func.coalesce(
                        func.sum(
                            SaleReturnItem
                            .r_quantity
                        ),
                        0,
                    )
                )
                .join(
                    SaleReturn,
                    SaleReturnItem
                    .sale_return_id
                    == SaleReturn.id,
                )
                .filter(
                    SaleReturn.sale_id
                    == sale.id,

                    SaleReturnItem.variant_id
                    == item.variant_id,

                    SaleReturn.status
                    == "Completed",
                )
                .scalar()
            )

            previous_k = int(
                previous_k or 0
            )

            previous_r = int(
                previous_r or 0
            )

            # ----------------------------------------------
            # Remaining Returnable
            # ----------------------------------------------

            remaining_k = (
                sale_item.k_quantity
                - previous_k
            )

            remaining_r = (
                sale_item.r_quantity
                - previous_r
            )

            if remaining_k < 0:
                remaining_k = 0

            if remaining_r < 0:
                remaining_r = 0

            # ----------------------------------------------
            # Validate K Return
            # ----------------------------------------------

            if (
                item.k_quantity
                > remaining_k
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot return "
                        f"{item.k_quantity} K "
                        f"units for Variant "
                        f"{item.variant_id}. "
                        f"Only {remaining_k} "
                        f"K units are still "
                        f"returnable."
                    ),
                )

            # ----------------------------------------------
            # Validate R Return
            # ----------------------------------------------

            if (
                item.r_quantity
                > remaining_r
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot return "
                        f"{item.r_quantity} R "
                        f"units for Variant "
                        f"{item.variant_id}. "
                        f"Only {remaining_r} "
                        f"R units are still "
                        f"returnable."
                    ),
                )

            # =================================================
            # INCREASE K STOCK
            # =================================================

            if item.k_quantity > 0:

                k_before = int(
                    stock.k_stock or 0
                )

                stock.k_stock += (
                    item.k_quantity
                )

                k_after = int(
                    stock.k_stock or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=shop_id,
                    variant_id=variant.id,
                    movement_type=
                        "SALE_RETURN",
                    stock_type="K",
                    quantity=
                        item.k_quantity,
                    quantity_before=
                        k_before,
                    quantity_after=
                        k_after,
                    reference_type=
                        "SALE_RETURN",
                    reference_id=
                        sale_return.id,
                    reference_number=
                        sale_return
                        .return_number,
                    reason=
                        sale_return.reason,
                )

            # =================================================
            # INCREASE R STOCK
            # =================================================

            if item.r_quantity > 0:

                r_before = int(
                    stock.r_stock or 0
                )

                stock.r_stock += (
                    item.r_quantity
                )

                r_after = int(
                    stock.r_stock or 0
                )

                record_stock_movement(
                    db=db,
                    shop_id=shop_id,
                    variant_id=variant.id,
                    movement_type=
                        "SALE_RETURN",
                    stock_type="R",
                    quantity=
                        item.r_quantity,
                    quantity_before=
                        r_before,
                    quantity_after=
                        r_after,
                    reference_type=
                        "SALE_RETURN",
                    reference_id=
                        sale_return.id,
                    reference_number=
                        sale_return
                        .return_number,
                    reason=
                        sale_return.reason,
                )

            # ----------------------------------------------
            # Calculate Refund
            # ----------------------------------------------

            item_refund = (
                Decimal(
                    str(
                        sale_item.unit_price
                    )
                )
                * Decimal(
                    item.quantity
                )
            )

            # ----------------------------------------------
            # Create Return Item
            # ----------------------------------------------

            return_item = (
                SaleReturnItem(
                    sale_return_id=
                        sale_return.id,

                    variant_id=
                        variant.id,

                    quantity=
                        item.quantity,

                    k_quantity=
                        item.k_quantity,

                    r_quantity=
                        item.r_quantity,

                    unit_price=
                        sale_item.unit_price,

                    refund_amount=
                        item_refund,
                )
            )

            db.add(
                return_item
            )

        # --------------------------------------------------
        # Commit
        # --------------------------------------------------

        db.commit()

        db.refresh(
            sale_return
        )

        return sale_return

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Sale return creation "
                f"failed: {str(exc)}"
            ),
        )


# ==========================================================
# GET ALL SALE RETURNS
# ==========================================================

def get_all_sale_returns(
    db: Session,
    shop_id: int,
):

    return (
        db.query(
            SaleReturn
        )
        .options(
            joinedload(
                SaleReturn.customer
            ),

            joinedload(
                SaleReturn.sale
            ),

            joinedload(
                SaleReturn.items
            )
            .joinedload(
                SaleReturnItem.variant
            ),
        )
        .filter(
            SaleReturn.shop_id
            == shop_id,
        )
        .order_by(
            SaleReturn.created_at.desc()
        )
        .all()
    )


# ==========================================================
# GET RETURN DETAILS
# ==========================================================

def get_sale_return_by_id(
    db: Session,
    shop_id: int,
    return_id: int,
):

    return (
        db.query(
            SaleReturn
        )
        .options(
            joinedload(
                SaleReturn.customer
            ),

            joinedload(
                SaleReturn.sale
            ),

            joinedload(
                SaleReturn.items
            )
            .joinedload(
                SaleReturnItem.variant
            ),
        )
        .filter(
            SaleReturn.id
            == return_id,

            SaleReturn.shop_id
            == shop_id,
        )
        .first()
    )