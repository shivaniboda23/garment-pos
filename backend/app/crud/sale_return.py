from datetime import datetime
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

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
from app.models.product import Product
from app.models.stock import Stock
from app.models.bill import Bill
from app.models.bill_item import BillItem

from app.services.stock_movement import (
    record_stock_movement,
)
from app.services.customer_receivable import (
    sync_bill_payment_status,
)


RECEIVABLE_ERROR = (
    "Customer receivable accounting integrity check failed."
)


def _validate_sale_return_customer(
    sale_customer_id,
    requested_customer_id,
) -> None:
    if sale_customer_id != requested_customer_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Customer does not match "
                "the selected sale."
            ),
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
    try:
        money_unit = Decimal("0.01")

        # The Sale row serializes every financial return for
        # this sale before any historical totals are read.
        sale = (
            db.query(Sale)
            .filter(
                Sale.id == data.sale_id,
                Sale.shop_id == shop_id,
            )
            .with_for_update(of=Sale)
            .first()
        )

        if not sale:
            raise HTTPException(
                status_code=404,
                detail="Sale not found.",
            )

        # The linked Bill is the shared receivable lock used by
        # customer payments. Legacy Sales without Bills continue
        # through the existing return path.
        bill = (
            db.query(Bill)
            .filter(Bill.sale_id == sale.id)
            .with_for_update(of=Bill)
            .first()
        )

        if bill and (
            bill.shop_id != shop_id
            or bill.customer_id != sale.customer_id
        ):
            raise HTTPException(
                status_code=500,
                detail=RECEIVABLE_ERROR,
            )

        _validate_sale_return_customer(
            sale_customer_id=sale.customer_id,
            requested_customer_id=data.customer_id,
        )

        if not data.items:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one return "
                    "item is required."
                ),
            )

        if Decimal(str(data.refund_amount)) < 0:
            raise HTTPException(
                status_code=400,
                detail="Refund amount cannot be negative.",
            )

        variant_ids = [
            item.variant_id
            for item in data.items
        ]

        if len(variant_ids) != len(set(variant_ids)):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Duplicate variant in "
                    "sale return items."
                ),
            )

        requested_items = sorted(
            data.items,
            key=lambda item: item.variant_id,
        )

        # Lock every SaleItem in a deterministic order. A
        # duplicate historical variant is ambiguous and must
        # never be resolved by selecting an arbitrary row.
        sale_items = (
            db.query(SaleItem)
            .filter(SaleItem.sale_id == sale.id)
            .order_by(
                SaleItem.variant_id.asc(),
                SaleItem.id.asc(),
            )
            .with_for_update(of=SaleItem)
            .all()
        )

        sale_items_by_variant = {}

        for sale_item in sale_items:
            if sale_item.variant_id in sale_items_by_variant:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Sale contains ambiguous duplicate "
                        "variant items."
                    ),
                )

            sale_items_by_variant[
                sale_item.variant_id
            ] = sale_item

        for item in requested_items:
            if item.variant_id not in sale_items_by_variant:
                raise HTTPException(
                    status_code=404,
                    detail="Variant not found in Sale.",
                )

        # Modern bills provide the authoritative ordered
        # quantity. Sales without a Bill use their historical
        # delivered SaleItem quantity as the legacy fallback.
        bill_items_by_variant = {}

        if bill:
            bill_items = (
                db.query(BillItem)
                .filter(BillItem.bill_id == bill.id)
                .order_by(
                    BillItem.variant_id.asc(),
                    BillItem.id.asc(),
                )
                .all()
            )

            for bill_item in bill_items:
                if bill_item.variant_id in bill_items_by_variant:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Bill contains ambiguous duplicate "
                            "variant items."
                        ),
                    )

                bill_items_by_variant[
                    bill_item.variant_id
                ] = bill_item

        historical_rows = (
            db.query(
                SaleReturnItem.variant_id,
                func.coalesce(
                    func.sum(SaleReturnItem.quantity),
                    0,
                ).label("quantity"),
                func.coalesce(
                    func.sum(SaleReturnItem.k_quantity),
                    0,
                ).label("k_quantity"),
                func.coalesce(
                    func.sum(SaleReturnItem.r_quantity),
                    0,
                ).label("r_quantity"),
            )
            .join(
                SaleReturn,
                SaleReturnItem.sale_return_id
                == SaleReturn.id,
            )
            .filter(
                SaleReturn.shop_id == shop_id,
                SaleReturn.sale_id == sale.id,
                SaleReturn.status == "Completed",
            )
            .group_by(SaleReturnItem.variant_id)
            .all()
        )

        historical_by_variant = {
            row.variant_id: {
                "quantity": int(row.quantity or 0),
                "k_quantity": int(row.k_quantity or 0),
                "r_quantity": int(row.r_quantity or 0),
            }
            for row in historical_rows
        }

        economic_rows = {}
        total_remaining_economic_qty = 0
        total_remaining_weight = Decimal("0")

        for variant_id, sale_item in (
            sale_items_by_variant.items()
        ):
            if bill:
                bill_item = bill_items_by_variant.get(
                    variant_id
                )

                if not bill_item:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Bill item is missing for a "
                            "sale variant."
                        ),
                    )

                economic_ordered_qty = int(
                    bill_item.ordered_qty or 0
                )
            else:
                economic_ordered_qty = int(
                    sale_item.quantity or 0
                )

            if economic_ordered_qty <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Sale item has invalid economic "
                        "quantity."
                    ),
                )

            line_total = Decimal(
                str(sale_item.total_price or 0)
            )

            if line_total < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Sale item has invalid economic "
                        "value."
                    ),
                )

            historical = historical_by_variant.get(
                variant_id,
                {
                    "quantity": 0,
                    "k_quantity": 0,
                    "r_quantity": 0,
                },
            )
            historical_quantity = historical["quantity"]

            if historical_quantity > economic_ordered_qty:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Historical return quantity is "
                        "inconsistent with the sale."
                    ),
                )

            remaining_economic_qty = (
                economic_ordered_qty
                - historical_quantity
            )
            unit_weight = (
                line_total
                / Decimal(economic_ordered_qty)
            )
            remaining_weight = (
                Decimal(remaining_economic_qty)
                * unit_weight
            )

            economic_rows[variant_id] = {
                "sale_item": sale_item,
                "historical": historical,
                "remaining_economic_qty": (
                    remaining_economic_qty
                ),
                "unit_weight": unit_weight,
                "remaining_weight": remaining_weight,
            }
            total_remaining_economic_qty += (
                remaining_economic_qty
            )
            total_remaining_weight += remaining_weight

        # Quantity is used only when every remaining economic
        # line is zero-valued. Positive lines retain their true
        # relative economic weight.
        if (
            total_remaining_economic_qty > 0
            and total_remaining_weight == 0
        ):
            total_remaining_weight = Decimal("0")

            for row in economic_rows.values():
                if row["remaining_economic_qty"] > 0:
                    row["unit_weight"] = Decimal("1")
                    row["remaining_weight"] = Decimal(
                        row["remaining_economic_qty"]
                    )
                    total_remaining_weight += row[
                        "remaining_weight"
                    ]

        requested_quantity_by_variant = {
            item.variant_id: item.quantity
            for item in requested_items
        }
        requested_weight_by_variant = {}
        requested_total_weight = Decimal("0")

        for item in requested_items:
            row = economic_rows[item.variant_id]

            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Return quantity must be greater "
                        "than zero."
                    ),
                )

            if item.k_quantity < 0 or item.r_quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Return stock quantity cannot be "
                        "negative."
                    ),
                )

            if item.quantity != (
                item.k_quantity + item.r_quantity
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Quantity must equal K Quantity + "
                        "R Quantity."
                    ),
                )

            if item.quantity > row["remaining_economic_qty"]:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Return quantity exceeds the "
                        "remaining economic quantity for "
                        f"Variant {item.variant_id}."
                    ),
                )

            item_weight = (
                Decimal(item.quantity)
                * row["unit_weight"]
            )
            requested_weight_by_variant[
                item.variant_id
            ] = item_weight
            requested_total_weight += item_weight

        # Lock requested variants and stocks in global ID order
        # before any inventory mutation.
        locked_variants = (
            db.query(ProductVariant)
            .join(
                Product,
                Product.id == ProductVariant.product_id,
            )
            .filter(
                ProductVariant.id.in_(variant_ids),
                Product.shop_id == shop_id,
            )
            .order_by(ProductVariant.id.asc())
            .with_for_update(of=ProductVariant)
            .all()
        )
        variants_by_id = {
            variant.id: variant
            for variant in locked_variants
        }

        if len(variants_by_id) != len(variant_ids):
            raise HTTPException(
                status_code=404,
                detail="Variant not found.",
            )

        locked_stocks = (
            db.query(Stock)
            .filter(Stock.variant_id.in_(variant_ids))
            .order_by(Stock.variant_id.asc())
            .with_for_update(of=Stock)
            .all()
        )
        stocks_by_variant = {
            stock.variant_id: stock
            for stock in locked_stocks
        }

        if len(stocks_by_variant) != len(variant_ids):
            raise HTTPException(
                status_code=500,
                detail="Stock record not found for variant.",
            )

        for item in requested_items:
            row = economic_rows[item.variant_id]
            sale_item = row["sale_item"]
            historical = row["historical"]
            remaining_k = max(
                int(sale_item.k_quantity or 0)
                - historical["k_quantity"],
                0,
            )
            remaining_r = max(
                int(sale_item.r_quantity or 0)
                - historical["r_quantity"],
                0,
            )

            if item.k_quantity > remaining_k:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot return {item.k_quantity} K "
                        f"units for Variant {item.variant_id}. "
                        f"Only {remaining_k} K units are "
                        "still returnable."
                    ),
                )

            if item.r_quantity > remaining_r:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot return {item.r_quantity} R "
                        f"units for Variant {item.variant_id}. "
                        f"Only {remaining_r} R units are "
                        "still returnable."
                    ),
                )

        historical_refund_total = Decimal(
            str(
                db.query(
                    func.coalesce(
                        func.sum(SaleReturn.refund_amount),
                        0,
                    )
                )
                .filter(
                    SaleReturn.shop_id == shop_id,
                    SaleReturn.sale_id == sale.id,
                    SaleReturn.status == "Completed",
                )
                .scalar()
                or 0
            )
        )
        sale_total = Decimal(str(sale.total_amount or 0))

        if sale_total < 0:
            raise HTTPException(
                status_code=400,
                detail="Sale has invalid economic value.",
            )

        remaining_refund_pool = max(
            sale_total - historical_refund_total,
            Decimal("0.00"),
        )
        all_remaining_returned = all(
            requested_quantity_by_variant.get(
                variant_id,
                0,
            ) == row["remaining_economic_qty"]
            for variant_id, row in economic_rows.items()
        )

        if remaining_refund_pool <= 0:
            authoritative_refund = Decimal("0.00")
        elif all_remaining_returned:
            authoritative_refund = remaining_refund_pool
        elif requested_total_weight <= 0:
            authoritative_refund = Decimal("0.00")
        else:
            if total_remaining_weight <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Remaining sale value cannot be "
                        "allocated safely."
                    ),
                )

            authoritative_refund = (
                remaining_refund_pool
                * requested_total_weight
                / total_remaining_weight
            ).quantize(
                money_unit,
                rounding=ROUND_HALF_UP,
            )

            if authoritative_refund > remaining_refund_pool:
                difference = (
                    authoritative_refund
                    - remaining_refund_pool
                )

                if difference <= money_unit:
                    authoritative_refund = (
                        remaining_refund_pool
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Calculated refund exceeds the "
                            "remaining sale value."
                        ),
                    )

        item_refunds = {}
        allocated_refund = Decimal("0.00")

        residue_variant_id = None

        if requested_total_weight > 0:
            residue_variant_id = max(
                variant_id
                for variant_id, weight in (
                    requested_weight_by_variant.items()
                )
                if weight > 0
            )

        for item in requested_items:
            item_refund = Decimal("0.00")

            if (
                authoritative_refund > 0
                and item.variant_id != residue_variant_id
                and requested_weight_by_variant[
                    item.variant_id
                ] > 0
            ):
                item_refund = (
                    authoritative_refund
                    * requested_weight_by_variant[
                        item.variant_id
                    ]
                    / requested_total_weight
                ).quantize(
                    money_unit,
                    rounding=ROUND_DOWN,
                )

            item_refunds[item.variant_id] = item_refund
            allocated_refund += item_refund

        if residue_variant_id is not None:
            item_refunds[residue_variant_id] = (
                authoritative_refund
                - allocated_refund
            )

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
        # Create Return Header after every validation succeeds.
        # --------------------------------------------------

        sale_return = SaleReturn(
            shop_id=shop_id,
            sale_id=sale.id,
            customer_id=sale.customer_id,
            return_number=return_number,
            reason=data.reason,
            refund_amount=authoritative_refund,
            status="Completed",
        )

        db.add(
            sale_return
        )

        db.flush()

        if bill:
            try:
                sync_bill_payment_status(
                    db=db,
                    shop_id=shop_id,
                    bill=bill,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=RECEIVABLE_ERROR,
                ) from exc

        # ==================================================
        # APPLY VALIDATED STOCK AND CREATE RETURN ITEMS
        # ==================================================

        for item in requested_items:
            sale_item = sale_items_by_variant[item.variant_id]
            variant = variants_by_id[item.variant_id]
            stock = stocks_by_variant[item.variant_id]

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
                        item_refunds[
                            item.variant_id
                        ],
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

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Sale return creation "
                "could not be completed."
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
