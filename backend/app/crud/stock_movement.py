from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.stock import Stock

from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem

from app.models.purchase_return import PurchaseReturn
from app.models.purchase_return_item import (
    PurchaseReturnItem,
)

from app.models.sale import Sale
from app.models.sale_item import SaleItem

from app.models.sale_return import SaleReturn
from app.models.sale_return_item import (
    SaleReturnItem,
)

from app.models.stock_movement import StockMovement

from app.schemas.stock_movement import (
    StockAdjustmentCreate,
)

from app.services.stock_movement import (
    record_stock_movement,
)


# ==========================================================
# HELPERS
# ==========================================================

def _timestamp_value(
    value,
):
    if value is None:
        return 0.0

    try:
        return value.timestamp()
    except Exception:
        return 0.0


def _clean_stock_type(
    value,
):
    stock_type = (
        str(value or "")
        .strip()
        .upper()
    )

    if stock_type not in (
        "K",
        "R",
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid historical stock type "
                f"'{value}'. Expected K or R."
            ),
        )

    return stock_type


# ==========================================================
# GET ALL STOCK MOVEMENTS
# ==========================================================

def get_stock_movements(
    db: Session,
    shop_id: int,
    variant_id: int | None = None,
    movement_type: str | None = None,
    stock_type: str | None = None,
):

    query = (
        db.query(StockMovement)
        .filter(
            StockMovement.shop_id
            == shop_id,
        )
    )

    if variant_id is not None:

        query = query.filter(
            StockMovement.variant_id
            == variant_id
        )

    if movement_type:

        clean_movement_type = (
            movement_type
            .strip()
            .upper()
        )

        query = query.filter(
            StockMovement.movement_type
            == clean_movement_type
        )

    if stock_type:

        clean_stock_type = (
            stock_type
            .strip()
            .upper()
        )

        if clean_stock_type not in (
            "K",
            "R",
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Stock type must be K or R."
                ),
            )

        query = query.filter(
            StockMovement.stock_type
            == clean_stock_type
        )

    return (
        query
        .order_by(
            StockMovement.created_at.desc(),
            StockMovement.id.desc(),
        )
        .all()
    )


# ==========================================================
# GET MOVEMENTS FOR ONE VARIANT
# ==========================================================

def get_variant_stock_movements(
    db: Session,
    shop_id: int,
    variant_id: int,
):

    variant = (
        db.query(ProductVariant)
        .join(
            Product,
            Product.id
            == ProductVariant.product_id,
        )
        .filter(
            ProductVariant.id
            == variant_id,

            Product.shop_id
            == shop_id,
        )
        .first()
    )

    if not variant:

        raise HTTPException(
            status_code=404,
            detail="Variant not found.",
        )

    return (
        db.query(StockMovement)
        .filter(
            StockMovement.shop_id
            == shop_id,

            StockMovement.variant_id
            == variant_id,
        )
        .order_by(
            StockMovement.created_at.desc(),
            StockMovement.id.desc(),
        )
        .all()
    )


# ==========================================================
# MANUAL STOCK ADJUSTMENT
# ==========================================================

def create_stock_adjustment(
    db: Session,
    shop_id: int,
    data: StockAdjustmentCreate,
):

    stock_type = (
        data.stock_type
        .strip()
        .upper()
    )

    if stock_type not in (
        "K",
        "R",
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Stock type must be K or R."
            ),
        )

    if data.quantity == 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Adjustment quantity "
                "cannot be zero."
            ),
        )

    reason = (
        data.reason
        .strip()
    )

    if not reason:

        raise HTTPException(
            status_code=400,
            detail="Reason is required.",
        )

    # ------------------------------------------------------
    # Validate Variant
    # ------------------------------------------------------

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
        .with_for_update(of=ProductVariant)
        .first()
    )

    if not variant:

        raise HTTPException(
            status_code=404,
            detail="Variant not found.",
        )

    # ------------------------------------------------------
    # Lock Stock
    # ------------------------------------------------------

    stock = (
        db.query(Stock)
        .filter(
            Stock.variant_id
            == variant.id
        )
        .with_for_update(of=Stock)
        .first()
    )

    if not stock:

        raise HTTPException(
            status_code=500,
            detail=(
                "Stock record not found."
            ),
        )

    # ------------------------------------------------------
    # K STOCK
    # ------------------------------------------------------

    if stock_type == "K":

        before = int(
            stock.k_stock or 0
        )

        after = (
            before
            + data.quantity
        )

        if after < 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"K stock cannot become "
                    f"negative. Available: "
                    f"{before}."
                ),
            )

        stock.k_stock = after

    # ------------------------------------------------------
    # R STOCK
    # ------------------------------------------------------

    else:

        before = int(
            stock.r_stock or 0
        )

        after = (
            before
            + data.quantity
        )

        if after < 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"R stock cannot become "
                    f"negative. Available: "
                    f"{before}."
                ),
            )

        stock.r_stock = after

    # ------------------------------------------------------
    # Movement
    # ------------------------------------------------------

    movement = (
        record_stock_movement(
            db=db,

            shop_id=shop_id,

            variant_id=
                variant.id,

            movement_type=
                "ADJUSTMENT",

            stock_type=
                stock_type,

            quantity=
                data.quantity,

            quantity_before=
                before,

            quantity_after=
                after,

            reference_type=
                "MANUAL",

            reference_id=
                None,

            reference_number=
                None,

            reason=
                reason,

            notes=
                data.notes,
        )
    )

    try:

        db.commit()

        db.refresh(
            movement
        )

        return movement

    except HTTPException:

        db.rollback()
        raise

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Stock adjustment could not be completed.",
        )


# ==========================================================
# HISTORICAL STOCK MOVEMENT BACKFILL
# ==========================================================

def backfill_stock_movements(
    db: Session,
    shop_id: int,
):
    """
    ONE-TIME historical stock movement reconstruction.

    This function DOES NOT modify current stock.

    Current stock from the stocks table is treated as the
    authoritative physical stock balance.

    Historical movements are reconstructed from:

        PURCHASE
        SALE
        PURCHASE_RETURN
        SALE_RETURN

    When historical data cannot explain the current stock,
    an explicit RECONCILIATION movement is created.

    Example:

        Historical calculated stock = 5
        Actual current stock         = 4

        Reconciliation              = -1

    This is safer than inventing negative opening stock.
    """

    # ======================================================
    # 1. DUPLICATE PROTECTION
    # ======================================================

    existing_count = (
        db.query(StockMovement)
        .filter(
            StockMovement.shop_id
            == shop_id,
        )
        .count()
    )

    if existing_count > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Stock movement history already "
                f"exists for this shop "
                f"({existing_count} rows). "
                "Historical backfill can only "
                "run when there are zero "
                "existing movement rows."
            ),
        )

    # ======================================================
    # 2. LOAD ALL VARIANTS
    # ======================================================

    variant_rows = (
        db.query(
            ProductVariant.id.label(
                "variant_id"
            ),

            ProductVariant.sku.label(
                "sku"
            ),
        )
        .join(
            Product,
            Product.id
            == ProductVariant.product_id,
        )
        .filter(
            Product.shop_id
            == shop_id,
        )
        .all()
    )

    if not variant_rows:

        raise HTTPException(
            status_code=400,
            detail=(
                "No variants found "
                "for this shop."
            ),
        )

    sku_by_variant = {
        int(row.variant_id):
            str(row.sku or "")
        for row in variant_rows
    }

    variant_ids = list(
        sku_by_variant.keys()
    )

    # ======================================================
    # 3. LOAD CURRENT STOCK
    # ======================================================

    stock_rows = (
        db.query(Stock)
        .filter(
            Stock.variant_id.in_(
                variant_ids
            )
        )
        .all()
    )

    stock_by_variant = {
        int(row.variant_id):
            row
        for row in stock_rows
    }

    missing_stock_variants = [
        variant_id
        for variant_id
        in variant_ids
        if variant_id
        not in stock_by_variant
    ]

    if missing_stock_variants:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    (
                        "Some variants do not have "
                        "stock records."
                    ),

                "variant_ids":
                    missing_stock_variants,
            },
        )

    current_stock = {}

    for variant_id in variant_ids:

        stock = (
            stock_by_variant[
                variant_id
            ]
        )

        current_stock[
            (
                variant_id,
                "K",
            )
        ] = int(
            stock.k_stock or 0
        )

        current_stock[
            (
                variant_id,
                "R",
            )
        ] = int(
            stock.r_stock or 0
        )

    # ======================================================
    # 4. COLLECT HISTORICAL EVENTS
    # ======================================================

    events = []

    # ======================================================
    # PURCHASE EVENTS
    # ======================================================

    purchase_rows = (
        db.query(
            Purchase,
            PurchaseItem,
        )
        .join(
            PurchaseItem,
            PurchaseItem.purchase_id
            == Purchase.id,
        )
        .filter(
            Purchase.shop_id
            == shop_id,
        )
        .all()
    )

    for (
        purchase,
        item,
    ) in purchase_rows:

        stock_type = (
            _clean_stock_type(
                item.stock_type
            )
        )

        quantity = int(
            item.quantity or 0
        )

        if quantity <= 0:
            continue

        events.append(
            {
                "variant_id":
                    int(
                        item.variant_id
                    ),

                "stock_type":
                    stock_type,

                "quantity":
                    quantity,

                "movement_type":
                    "PURCHASE",

                "reference_type":
                    "PURCHASE",

                "reference_id":
                    purchase.id,

                "reference_number":
                    purchase.invoice_number,

                "reason":
                    None,

                "notes":
                    (
                        "Historical movement "
                        "reconstructed from purchase."
                    ),

                "created_at":
                    purchase.created_at,

                "item_id":
                    item.id,
            }
        )

    # ======================================================
    # SALE EVENTS
    # ======================================================

    sale_rows = (
        db.query(
            Sale,
            SaleItem,
        )
        .join(
            SaleItem,
            SaleItem.sale_id
            == Sale.id,
        )
        .filter(
            Sale.shop_id
            == shop_id,

            Sale.status
            == "Completed",
        )
        .all()
    )

    for (
        sale,
        item,
    ) in sale_rows:

        k_quantity = int(
            item.k_quantity or 0
        )

        r_quantity = int(
            item.r_quantity or 0
        )

        if k_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "K",

                    "quantity":
                        -k_quantity,

                    "movement_type":
                        "SALE",

                    "reference_type":
                        "SALE",

                    "reference_id":
                        sale.id,

                    "reference_number":
                        sale.invoice_number,

                    "reason":
                        None,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from sale."
                        ),

                    "created_at":
                        sale.created_at,

                    "item_id":
                        item.id,
                }
            )

        if r_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "R",

                    "quantity":
                        -r_quantity,

                    "movement_type":
                        "SALE",

                    "reference_type":
                        "SALE",

                    "reference_id":
                        sale.id,

                    "reference_number":
                        sale.invoice_number,

                    "reason":
                        None,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from sale."
                        ),

                    "created_at":
                        sale.created_at,

                    "item_id":
                        item.id,
                }
            )

    # ======================================================
    # PURCHASE RETURN EVENTS
    # ======================================================

    purchase_return_rows = (
        db.query(
            PurchaseReturn,
            PurchaseReturnItem,
        )
        .join(
            PurchaseReturnItem,

            PurchaseReturnItem
            .purchase_return_id
            == PurchaseReturn.id,
        )
        .filter(
            PurchaseReturn.shop_id
            == shop_id,

            PurchaseReturn.status
            == "Completed",
        )
        .all()
    )

    for (
        purchase_return,
        item,
    ) in purchase_return_rows:

        k_quantity = int(
            item.k_quantity or 0
        )

        r_quantity = int(
            item.r_quantity or 0
        )

        if k_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "K",

                    "quantity":
                        -k_quantity,

                    "movement_type":
                        "PURCHASE_RETURN",

                    "reference_type":
                        "PURCHASE_RETURN",

                    "reference_id":
                        purchase_return.id,

                    "reference_number":
                        purchase_return
                        .return_number,

                    "reason":
                        purchase_return.reason,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from "
                            "purchase return."
                        ),

                    "created_at":
                        purchase_return
                        .created_at,

                    "item_id":
                        item.id,
                }
            )

        if r_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "R",

                    "quantity":
                        -r_quantity,

                    "movement_type":
                        "PURCHASE_RETURN",

                    "reference_type":
                        "PURCHASE_RETURN",

                    "reference_id":
                        purchase_return.id,

                    "reference_number":
                        purchase_return
                        .return_number,

                    "reason":
                        purchase_return.reason,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from "
                            "purchase return."
                        ),

                    "created_at":
                        purchase_return
                        .created_at,

                    "item_id":
                        item.id,
                }
            )

    # ======================================================
    # SALE RETURN EVENTS
    # ======================================================

    sale_return_rows = (
        db.query(
            SaleReturn,
            SaleReturnItem,
        )
        .join(
            SaleReturnItem,

            SaleReturnItem
            .sale_return_id
            == SaleReturn.id,
        )
        .filter(
            SaleReturn.shop_id
            == shop_id,

            SaleReturn.status
            == "Completed",
        )
        .all()
    )

    for (
        sale_return,
        item,
    ) in sale_return_rows:

        k_quantity = int(
            item.k_quantity or 0
        )

        r_quantity = int(
            item.r_quantity or 0
        )

        if k_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "K",

                    "quantity":
                        k_quantity,

                    "movement_type":
                        "SALE_RETURN",

                    "reference_type":
                        "SALE_RETURN",

                    "reference_id":
                        sale_return.id,

                    "reference_number":
                        sale_return
                        .return_number,

                    "reason":
                        sale_return.reason,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from "
                            "sale return."
                        ),

                    "created_at":
                        sale_return.created_at,

                    "item_id":
                        item.id,
                }
            )

        if r_quantity > 0:

            events.append(
                {
                    "variant_id":
                        int(
                            item.variant_id
                        ),

                    "stock_type":
                        "R",

                    "quantity":
                        r_quantity,

                    "movement_type":
                        "SALE_RETURN",

                    "reference_type":
                        "SALE_RETURN",

                    "reference_id":
                        sale_return.id,

                    "reference_number":
                        sale_return
                        .return_number,

                    "reason":
                        sale_return.reason,

                    "notes":
                        (
                            "Historical movement "
                            "reconstructed from "
                            "sale return."
                        ),

                    "created_at":
                        sale_return.created_at,

                    "item_id":
                        item.id,
                }
            )

    # ======================================================
    # 5. GROUP EVENTS BY VARIANT + STOCK TYPE
    # ======================================================

    grouped_events = {}

    for event in events:

        key = (
            event[
                "variant_id"
            ],
            event[
                "stock_type"
            ],
        )

        grouped_events.setdefault(
            key,
            [],
        ).append(
            event
        )

    # ======================================================
    # 6. BUILD FINAL MOVEMENT HISTORY
    # ======================================================

    final_rows = []

    reconciliation_details = []

    all_keys = []

    for variant_id in variant_ids:

        all_keys.append(
            (
                variant_id,
                "K",
            )
        )

        all_keys.append(
            (
                variant_id,
                "R",
            )
        )

    for key in all_keys:

        variant_id, stock_type = key

        actual_current = (
            current_stock[
                key
            ]
        )

        group = list(
            grouped_events.get(
                key,
                [],
            )
        )

        # --------------------------------------------------
        # NO HISTORICAL EVENTS
        # --------------------------------------------------

        if not group:

            if actual_current > 0:

                final_rows.append(
                    {
                        "variant_id":
                            variant_id,

                        "stock_type":
                            stock_type,

                        "quantity":
                            actual_current,

                        "quantity_before":
                            0,

                        "quantity_after":
                            actual_current,

                        "movement_type":
                            "OPENING_STOCK",

                        "reference_type":
                            "HISTORICAL",

                        "reference_id":
                            None,

                        "reference_number":
                            None,

                        "reason":
                            (
                                "Existing stock before "
                                "transaction history."
                            ),

                        "notes":
                            (
                                "Opening stock reconstructed "
                                "during historical backfill."
                            ),

                        "created_at":
                            datetime.now(
                                timezone.utc
                            ),
                    }
                )

            continue

        # --------------------------------------------------
        # Sort chronologically
        # --------------------------------------------------

        group.sort(
            key=lambda event: (
                _timestamp_value(
                    event[
                        "created_at"
                    ]
                ),

                int(
                    event[
                        "reference_id"
                    ]
                    or 0
                ),

                int(
                    event[
                        "item_id"
                    ]
                    or 0
                ),
            )
        )

        # --------------------------------------------------
        # Calculate total net movement
        # --------------------------------------------------

        total_net_movement = sum(
            int(
                event[
                    "quantity"
                ]
            )
            for event in group
        )

        calculated_opening = (
            actual_current
            - total_net_movement
        )

        # --------------------------------------------------
        # Determine minimum opening required so historical
        # running stock never becomes negative.
        # --------------------------------------------------

        cumulative = 0

        minimum_cumulative = 0

        for event in group:

            cumulative += int(
                event[
                    "quantity"
                ]
            )

            minimum_cumulative = min(
                minimum_cumulative,
                cumulative,
            )

        minimum_required_opening = max(
            0,
            -minimum_cumulative,
        )

        # --------------------------------------------------
        # Choose safe opening balance
        # --------------------------------------------------

        safe_opening = max(
            0,
            calculated_opening,
            minimum_required_opening,
        )

        earliest_time = (
            group[0][
                "created_at"
            ]
        )

        if earliest_time is None:

            earliest_time = (
                datetime.now(
                    timezone.utc
                )
            )

        # --------------------------------------------------
        # Opening stock
        # --------------------------------------------------

        running = 0

        if safe_opening > 0:

            opening_time = (
                earliest_time
                - timedelta(
                    microseconds=1
                )
            )

            final_rows.append(
                {
                    "variant_id":
                        variant_id,

                    "stock_type":
                        stock_type,

                    "quantity":
                        safe_opening,

                    "quantity_before":
                        0,

                    "quantity_after":
                        safe_opening,

                    "movement_type":
                        "OPENING_STOCK",

                    "reference_type":
                        "HISTORICAL",

                    "reference_id":
                        None,

                    "reference_number":
                        None,

                    "reason":
                        (
                            "Opening stock reconstructed "
                            "from historical transactions."
                        ),

                    "notes":
                        (
                            "System-generated historical "
                            "opening balance."
                        ),

                    "created_at":
                        opening_time,
                }
            )

            running = safe_opening

        # --------------------------------------------------
        # Historical transactions
        # --------------------------------------------------

        for event in group:

            quantity = int(
                event[
                    "quantity"
                ]
            )

            before = running

            after = (
                before
                + quantity
            )

            if after < 0:

                raise HTTPException(
                    status_code=400,
                    detail={
                        "message":
                            (
                                "Historical movement "
                                "reconstruction attempted "
                                "to create negative stock."
                            ),

                        "variant_id":
                            variant_id,

                        "sku":
                            sku_by_variant.get(
                                variant_id,
                                "",
                            ),

                        "stock_type":
                            stock_type,

                        "quantity_before":
                            before,

                        "movement_quantity":
                            quantity,

                        "quantity_after":
                            after,
                    },
                )

            final_rows.append(
                {
                    "variant_id":
                        variant_id,

                    "stock_type":
                        stock_type,

                    "quantity":
                        quantity,

                    "quantity_before":
                        before,

                    "quantity_after":
                        after,

                    "movement_type":
                        event[
                            "movement_type"
                        ],

                    "reference_type":
                        event[
                            "reference_type"
                        ],

                    "reference_id":
                        event[
                            "reference_id"
                        ],

                    "reference_number":
                        event[
                            "reference_number"
                        ],

                    "reason":
                        event[
                            "reason"
                        ],

                    "notes":
                        event[
                            "notes"
                        ],

                    "created_at":
                        event[
                            "created_at"
                        ],
                }
            )

            running = after

        # --------------------------------------------------
        # RECONCILIATION
        # --------------------------------------------------

        reconciliation_quantity = (
            actual_current
            - running
        )

        if reconciliation_quantity != 0:

            latest_time = (
                group[-1][
                    "created_at"
                ]
            )

            if latest_time is None:

                latest_time = (
                    datetime.now(
                        timezone.utc
                    )
                )

            reconciliation_time = (
                latest_time
                + timedelta(
                    microseconds=1
                )
            )

            reconciliation_after = (
                running
                + reconciliation_quantity
            )

            if reconciliation_after < 0:

                raise HTTPException(
                    status_code=400,
                    detail={
                        "message":
                            (
                                "Reconciliation would "
                                "produce negative stock."
                            ),

                        "variant_id":
                            variant_id,

                        "sku":
                            sku_by_variant.get(
                                variant_id,
                                "",
                            ),

                        "stock_type":
                            stock_type,

                        "before":
                            running,

                        "quantity":
                            reconciliation_quantity,

                        "after":
                            reconciliation_after,
                    },
                )

            final_rows.append(
                {
                    "variant_id":
                        variant_id,

                    "stock_type":
                        stock_type,

                    "quantity":
                        reconciliation_quantity,

                    "quantity_before":
                        running,

                    "quantity_after":
                        reconciliation_after,

                    "movement_type":
                        "RECONCILIATION",

                    "reference_type":
                        "HISTORICAL_RECONCILIATION",

                    "reference_id":
                        None,

                    "reference_number":
                        None,

                    "reason":
                        (
                            "Legacy stock balance "
                            "reconciliation."
                        ),

                    "notes":
                        (
                            "Historical transactions "
                            "could not fully explain "
                            "the current physical stock. "
                            "Current stock was preserved "
                            "as authoritative."
                        ),

                    "created_at":
                        reconciliation_time,
                }
            )

            reconciliation_details.append(
                {
                    "variant_id":
                        variant_id,

                    "sku":
                        sku_by_variant.get(
                            variant_id,
                            "",
                        ),

                    "stock_type":
                        stock_type,

                    "calculated_opening":
                        calculated_opening,

                    "safe_opening":
                        safe_opening,

                    "historical_closing_before_reconciliation":
                        running,

                    "actual_current_stock":
                        actual_current,

                    "reconciliation_quantity":
                        reconciliation_quantity,
                }
            )

            running = (
                reconciliation_after
            )

        # --------------------------------------------------
        # FINAL SAFETY CHECK
        # --------------------------------------------------

        if running != actual_current:

            raise HTTPException(
                status_code=500,
                detail={
                    "message":
                        (
                            "Final historical movement "
                            "balance does not equal "
                            "current stock."
                        ),

                    "variant_id":
                        variant_id,

                    "sku":
                        sku_by_variant.get(
                            variant_id,
                            "",
                        ),

                    "stock_type":
                        stock_type,

                    "calculated":
                        running,

                    "actual":
                        actual_current,
                },
            )

    # ======================================================
    # 7. SORT ALL ROWS
    # ======================================================

    final_rows.sort(
        key=lambda row: (
            _timestamp_value(
                row[
                    "created_at"
                ]
            ),

            row[
                "variant_id"
            ],

            row[
                "stock_type"
            ],
        )
    )

    # ======================================================
    # 8. INSERT INTO DATABASE
    # ======================================================

    counts = {
        "OPENING_STOCK": 0,
        "PURCHASE": 0,
        "SALE": 0,
        "PURCHASE_RETURN": 0,
        "SALE_RETURN": 0,
        "RECONCILIATION": 0,
    }

    try:

        for row in final_rows:

            movement = StockMovement(
                shop_id=
                    shop_id,

                variant_id=
                    row[
                        "variant_id"
                    ],

                movement_type=
                    row[
                        "movement_type"
                    ],

                stock_type=
                    row[
                        "stock_type"
                    ],

                quantity=
                    row[
                        "quantity"
                    ],

                quantity_before=
                    row[
                        "quantity_before"
                    ],

                quantity_after=
                    row[
                        "quantity_after"
                    ],

                reference_type=
                    row[
                        "reference_type"
                    ],

                reference_id=
                    row[
                        "reference_id"
                    ],

                reference_number=
                    row[
                        "reference_number"
                    ],

                reason=
                    row[
                        "reason"
                    ],

                notes=
                    row[
                        "notes"
                    ],

                created_at=
                    row[
                        "created_at"
                    ],
            )

            db.add(
                movement
            )

            movement_type = (
                row[
                    "movement_type"
                ]
            )

            counts[
                movement_type
            ] = (
                counts.get(
                    movement_type,
                    0,
                )
                + 1
            )

        db.commit()

        return {
            "success":
                True,

            "message":
                (
                    "Historical stock movements "
                    "backfilled successfully."
                ),

            "shop_id":
                shop_id,

            "total_movements":
                len(
                    final_rows
                ),

            "opening_stock_movements":
                counts.get(
                    "OPENING_STOCK",
                    0,
                ),

            "purchase_movements":
                counts.get(
                    "PURCHASE",
                    0,
                ),

            "sale_movements":
                counts.get(
                    "SALE",
                    0,
                ),

            "purchase_return_movements":
                counts.get(
                    "PURCHASE_RETURN",
                    0,
                ),

            "sale_return_movements":
                counts.get(
                    "SALE_RETURN",
                    0,
                ),

            "reconciliation_movements":
                counts.get(
                    "RECONCILIATION",
                    0,
                ),

            "reconciliations":
                reconciliation_details,
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Stock movement backfill "
                f"failed: {str(exc)}"
            ),
        )
