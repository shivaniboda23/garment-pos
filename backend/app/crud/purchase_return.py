from datetime import datetime
from decimal import Decimal, ROUND_DOWN

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
from app.models.product import Product
from app.models.stock import Stock

from app.services.stock_movement import (
    record_stock_movement,
)
from app.services.supplier_accounting import (
    sync_purchase_balance,
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
        .with_for_update(of=Purchase)
        .first()
    )

    if not purchase:
        raise ValueError(
            "Purchase not found."
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

    money_unit = Decimal("0.01")

    if Decimal(str(data.total_amount)) < 0:
        raise ValueError(
            "Submitted total amount cannot be negative."
        )

    variant_ids = [
        item.variant_id
        for item in data.items
    ]

    if len(variant_ids) != len(set(variant_ids)):
        raise ValueError(
            "Duplicate variant in purchase return items."
        )

    historical_items = (
        db.query(PurchaseItem)
        .filter(
            PurchaseItem.purchase_id == purchase.id,
        )
        .all()
    )
    historical_items_by_variant = {}
    buckets = {}

    for historical_item in historical_items:
        stock_type = (
            historical_item.stock_type or ""
        ).upper()

        if stock_type not in ("K", "R"):
            raise ValueError(
                f"Invalid stock type '{historical_item.stock_type}' "
                f"in Purchase Item {historical_item.id}."
            )

        quantity = int(historical_item.quantity or 0)
        cost_price = Decimal(
            str(historical_item.cost_price or 0)
        )
        discount = Decimal(
            str(historical_item.discount or 0)
        )
        gross_base = Decimal(quantity) * cost_price
        line_base = max(
            gross_base - discount,
            Decimal("0"),
        )
        bucket = buckets.setdefault(
            (historical_item.variant_id, stock_type),
            {
                "purchased_quantity": 0,
                "historical_base": Decimal("0"),
                "gross_base": Decimal("0"),
            },
        )
        bucket["purchased_quantity"] += quantity
        bucket["historical_base"] += line_base
        bucket["gross_base"] += gross_base
        historical_items_by_variant.setdefault(
            historical_item.variant_id,
            [],
        ).append(historical_item)

    returned_quantity_rows = (
        db.query(
            PurchaseReturnItem.variant_id,
            func.coalesce(
                func.sum(PurchaseReturnItem.k_quantity),
                0,
            ),
            func.coalesce(
                func.sum(PurchaseReturnItem.r_quantity),
                0,
            ),
        )
        .join(
            PurchaseReturn,
            PurchaseReturnItem.purchase_return_id
            == PurchaseReturn.id,
        )
        .filter(
            PurchaseReturn.shop_id == shop_id,
            PurchaseReturn.purchase_id == purchase.id,
            PurchaseReturn.status == "Completed",
        )
        .group_by(PurchaseReturnItem.variant_id)
        .all()
    )
    returned_quantities = {
        (variant_id, "K"): int(k_quantity or 0)
        for variant_id, k_quantity, _ in returned_quantity_rows
    }
    returned_quantities.update({
        (variant_id, "R"): int(r_quantity or 0)
        for variant_id, _, r_quantity in returned_quantity_rows
    })

    total_remaining_weight = Decimal("0")
    total_remaining_quantity = 0

    for bucket_key, bucket in buckets.items():
        purchased_quantity = bucket["purchased_quantity"]

        if purchased_quantity <= 0:
            raise ValueError(
                "Purchase contains an invalid item quantity."
            )

        if bucket["historical_base"] > 0:
            unit_weight = (
                bucket["historical_base"]
                / Decimal(purchased_quantity)
            )
        elif bucket["gross_base"] > 0:
            unit_weight = (
                bucket["gross_base"]
                / Decimal(purchased_quantity)
            )
        else:
            unit_weight = Decimal("1")

        remaining_quantity = max(
            purchased_quantity
            - returned_quantities.get(bucket_key, 0),
            0,
        )
        bucket["unit_weight"] = unit_weight
        bucket["remaining_quantity"] = remaining_quantity
        bucket["remaining_weight"] = (
            Decimal(remaining_quantity) * unit_weight
        )
        total_remaining_quantity += remaining_quantity
        total_remaining_weight += bucket["remaining_weight"]

    if (
        total_remaining_quantity > 0
        and total_remaining_weight <= 0
    ):
        raise ValueError(
            "Unable to calculate the remaining purchase return weight."
        )

    completed_return_total = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(PurchaseReturn.total_amount),
                    0,
                )
            )
            .filter(
                PurchaseReturn.shop_id == shop_id,
                PurchaseReturn.purchase_id == purchase.id,
                PurchaseReturn.status == "Completed",
            )
            .scalar()
            or 0
        )
    ).quantize(money_unit)

    purchase_total = Decimal(
        str(purchase.grand_total or 0)
    ).quantize(money_unit)
    remaining_return_pool = max(
        purchase_total - completed_return_total,
        Decimal("0.00"),
    )

    return_contexts = []
    requested_quantities = {}
    requested_total_weight = Decimal("0")

    for item in data.items:
        if item.quantity <= 0:
            raise ValueError(
                "Return quantity must be greater than zero."
            )

        if item.k_quantity < 0:
            raise ValueError(
                "K quantity cannot be negative."
            )

        if item.r_quantity < 0:
            raise ValueError(
                "R quantity cannot be negative."
            )

        if item.quantity != item.k_quantity + item.r_quantity:
            raise ValueError(
                "Quantity must equal K Quantity + R Quantity."
            )

        if Decimal(str(item.total)) < 0:
            raise ValueError(
                "Submitted return item total cannot be negative."
            )

        submitted_cost_price = Decimal(
            str(item.cost_price)
        )

        if submitted_cost_price < 0:
            raise ValueError(
                "Return item cost price cannot be negative."
            )

        purchase_items = historical_items_by_variant.get(
            item.variant_id,
            [],
        )

        if not purchase_items:
            raise ValueError(
                f"Variant {item.variant_id} was not purchased "
                f"in Purchase {purchase.id}."
            )

        historical_costs = {
            Decimal(str(purchase_item.cost_price or 0))
            .quantize(money_unit)
            for purchase_item in purchase_items
        }

        if submitted_cost_price.quantize(
            money_unit
        ) not in historical_costs:
            raise ValueError(
                "Return item cost price does not match "
                "the historical purchase cost."
            )

        requested_item_weight = Decimal("0")

        for stock_type, quantity in (
            ("K", item.k_quantity),
            ("R", item.r_quantity),
        ):
            bucket_key = (item.variant_id, stock_type)
            bucket = buckets.get(bucket_key)

            if quantity > 0 and not bucket:
                raise ValueError(
                    f"No {stock_type} units for Variant "
                    f"{item.variant_id} were purchased."
                )

            remaining_quantity = (
                bucket["remaining_quantity"]
                if bucket
                else 0
            )

            if quantity > remaining_quantity:
                raise ValueError(
                    f"Cannot return {quantity} {stock_type} units "
                    f"for Variant {item.variant_id}. Only "
                    f"{remaining_quantity} {stock_type} units "
                    "are still returnable."
                )

            if bucket:
                requested_item_weight += (
                    Decimal(quantity) * bucket["unit_weight"]
                )
                requested_quantities[bucket_key] = quantity

        variant = (
            db.query(ProductVariant)
            .join(
                Product,
                Product.id == ProductVariant.product_id,
            )
            .filter(
                ProductVariant.id == item.variant_id,
                Product.shop_id == shop_id,
            )
            .with_for_update(of=ProductVariant)
            .first()
        )

        if not variant:
            raise ValueError("Variant not found.")

        stock = (
            db.query(Stock)
            .filter(Stock.variant_id == variant.id)
            .with_for_update(of=Stock)
            .first()
        )

        if not stock:
            raise ValueError(
                f"No stock record found for Variant {variant.id}."
            )

        if item.k_quantity > stock.k_stock:
            raise ValueError(
                f"Not enough K Stock for SKU {variant.sku}. "
                f"Available: {stock.k_stock}, "
                f"Requested return: {item.k_quantity}."
            )

        if item.r_quantity > stock.r_stock:
            raise ValueError(
                f"Not enough R Stock for SKU {variant.sku}. "
                f"Available: {stock.r_stock}, "
                f"Requested return: {item.r_quantity}."
            )

        requested_total_weight += requested_item_weight
        return_contexts.append({
            "item": item,
            "variant": variant,
            "stock": stock,
            "weight": requested_item_weight,
        })

    if requested_total_weight <= 0:
        raise ValueError(
            "Unable to calculate the requested purchase return weight."
        )

    all_remaining_goods_returned = all(
        requested_quantities.get(bucket_key, 0)
        == bucket["remaining_quantity"]
        for bucket_key, bucket in buckets.items()
    )

    if remaining_return_pool == 0:
        authoritative_return_total = Decimal("0.00")
    elif all_remaining_goods_returned:
        authoritative_return_total = remaining_return_pool
    else:
        authoritative_return_total = (
            remaining_return_pool
            * requested_total_weight
            / total_remaining_weight
        ).quantize(money_unit)

    if authoritative_return_total > remaining_return_pool:
        rounding_difference = (
            authoritative_return_total - remaining_return_pool
        )

        if rounding_difference <= money_unit:
            authoritative_return_total = remaining_return_pool
        else:
            raise ValueError(
                "Calculated return total exceeds the remaining return pool."
            )

    authoritative_item_totals = {}
    allocated_total = Decimal("0.00")
    ordered_contexts = sorted(
        return_contexts,
        key=lambda context: context["item"].variant_id,
    )

    for context in ordered_contexts[:-1]:
        item_total = (
            authoritative_return_total
            * context["weight"]
            / requested_total_weight
        ).quantize(
            money_unit,
            rounding=ROUND_DOWN,
        )
        authoritative_item_totals[
            context["item"].variant_id
        ] = item_total
        allocated_total += item_total

    residue_context = ordered_contexts[-1]
    authoritative_item_totals[
        residue_context["item"].variant_id
    ] = authoritative_return_total - allocated_total

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
        total_amount=authoritative_return_total,
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

        for context in return_contexts:
            item = context["item"]
            variant = context["variant"]
            stock = context["stock"]

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
                        authoritative_item_totals[
                            item.variant_id
                        ],
                )
            )

            db.add(
                return_item
            )

        # ---------------------------------------------------
        # Synchronize Purchase Liability and Commit
        # ---------------------------------------------------

        db.flush()

        sync_purchase_balance(
            db=db,
            shop_id=shop_id,
            purchase=purchase,
        )

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
