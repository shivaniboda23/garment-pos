from decimal import Decimal
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sale import Sale
from app.models.sale_item import SaleItem

from app.models.sale_return import SaleReturn
from app.models.sale_return_item import SaleReturnItem

from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn

from app.models.expense import Expense
from app.models.tailoring_job import TailoringJob

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.stock import Stock


# ==========================================================
# HELPERS
# ==========================================================


def get_cogs_for_sales(
    db: Session,
    shop_id: int,
    sale_ids=None,
):
    """
    Calculate COGS from the historical cost snapshot
    stored in sale_items.

    Returns:
        (
            total_cogs,
            zero_cost_item_count
        )
    """

    query = (
        db.query(SaleItem)
        .join(
            Sale,
            Sale.id == SaleItem.sale_id,
        )
        .filter(
            Sale.shop_id == shop_id,
        )
    )

    if sale_ids is not None:
        if not sale_ids:
            return Decimal("0.00"), 0

        query = query.filter(
            SaleItem.sale_id.in_(sale_ids)
        )

    sale_items = query.all()

    total_cogs = Decimal("0.00")

    zero_cost_items = 0

    for item in sale_items:

        cost_price = Decimal(
            str(
                item.cost_price or 0
            )
        )

        if cost_price <= 0:
            zero_cost_items += 1

        total_cogs += (
            cost_price
            * Decimal(item.quantity)
        )

    return (
        total_cogs,
        zero_cost_items,
    )


def get_returned_cogs(
    db: Session,
    shop_id: int,
    sale_ids=None,
):
    """
    Calculate COGS associated with completed
    sales returns.
    """

    query = (
        db.query(
            SaleReturnItem,
            SaleItem.cost_price,
        )
        .join(
            SaleReturn,
            SaleReturnItem.sale_return_id
            == SaleReturn.id,
        )
        .join(
            SaleItem,
            (
                SaleItem.sale_id
                == SaleReturn.sale_id
            )
            & (
                SaleItem.variant_id
                == SaleReturnItem.variant_id
            ),
        )
        .filter(
            SaleReturn.shop_id == shop_id,
            SaleReturn.status == "Completed",
        )
    )

    if sale_ids is not None:

        if not sale_ids:
            return Decimal("0.00")

        query = query.filter(
            SaleReturn.sale_id.in_(sale_ids)
        )

    rows = query.all()

    returned_cogs = Decimal("0.00")

    for return_item, cost_price in rows:

        cost = Decimal(
            str(
                cost_price or 0
            )
        )

        returned_cogs += (
            cost
            * Decimal(
                return_item.quantity
            )
        )

    return returned_cogs


def get_sale_return_total(
    db: Session,
    shop_id: int,
    sale_ids=None,
):
    """
    Calculate refund amount from completed
    sales returns.
    """

    query = (
        db.query(
            func.coalesce(
                func.sum(
                    SaleReturn.refund_amount
                ),
                0,
            )
        )
        .filter(
            SaleReturn.shop_id == shop_id,
            SaleReturn.status == "Completed",
        )
    )

    if sale_ids is not None:

        if not sale_ids:
            return Decimal("0.00")

        query = query.filter(
            SaleReturn.sale_id.in_(sale_ids)
        )

    return Decimal(
        str(
            query.scalar() or 0
        )
    )


# ==========================================================
# TAILORING EXPENSE
# ==========================================================


def get_tailoring_expense(
    db: Session,
    shop_id: int,
    report_date=None,
    month: str | None = None,
):
    """
    Recognize the agreed total stitching charge once the
    tailor has returned at least one item for the job.

    Cancelled jobs are excluded. The first received_at date
    is used as the expense-recognition date.
    """

    query = (
        db.query(
            func.coalesce(
                func.sum(TailoringJob.stitching_charge),
                0,
            )
        )
        .filter(
            TailoringJob.shop_id == shop_id,
            TailoringJob.status != "Cancelled",
            TailoringJob.received_quantity > 0,
            TailoringJob.received_at.isnot(None),
        )
    )

    if report_date is not None:
        query = query.filter(
            func.date(TailoringJob.received_at) == report_date
        )

    if month is not None:
        query = query.filter(
            func.to_char(
                TailoringJob.received_at,
                "YYYY-MM",
            ) == month
        )

    return Decimal(str(query.scalar() or 0))


# ==========================================================
# PROFIT & LOSS
# ==========================================================


def get_profit_loss(
    db: Session,
    shop_id: int,
):
    # ------------------------------------------------------
    # SALES
    # ------------------------------------------------------

    total_sales = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Sale.total_amount
                    ),
                    0,
                )
            )
            .filter(
                Sale.shop_id == shop_id,
            )
            .scalar()
            or 0
        )
    )

    sales_return = get_sale_return_total(
        db=db,
        shop_id=shop_id,
    )

    net_sales = (
        total_sales
        - sales_return
    )

    # ------------------------------------------------------
    # COGS
    # ------------------------------------------------------

    total_cogs, zero_cost_items = (
        get_cogs_for_sales(
            db=db,
            shop_id=shop_id,
        )
    )

    returned_cogs = get_returned_cogs(
        db=db,
        shop_id=shop_id,
    )

    net_cogs = (
        total_cogs
        - returned_cogs
    )

    if net_cogs < 0:
        net_cogs = Decimal(
            "0.00"
        )

    # ------------------------------------------------------
    # PURCHASES
    # ------------------------------------------------------

    total_purchase = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Purchase.grand_total
                    ),
                    0,
                )
            )
            .filter(
                Purchase.shop_id == shop_id,
            )
            .scalar()
            or 0
        )
    )

    purchase_return = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        PurchaseReturn.total_amount
                    ),
                    0,
                )
            )
            .filter(
                PurchaseReturn.shop_id == shop_id,
                PurchaseReturn.status
                == "Completed",
            )
            .scalar()
            or 0
        )
    )

    net_purchase = (
        total_purchase
        - purchase_return
    )

    # ------------------------------------------------------
    # EXPENSES
    # ------------------------------------------------------

    operating_expense = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(Expense.amount),
                    0,
                )
            )
            .filter(
                Expense.shop_id == shop_id,
            )
            .scalar()
            or 0
        )
    )

    tailoring_expense = get_tailoring_expense(
        db=db,
        shop_id=shop_id,
    )

    total_expense = (
        operating_expense
        + tailoring_expense
    )

    # ------------------------------------------------------
    # PROFIT
    # ------------------------------------------------------

    gross_profit = (
        net_sales
        - net_cogs
    )

    net_profit = (
        gross_profit
        - total_expense
    )

    if net_sales > 0:

        profit_margin = float(
            round(
                (
                    net_profit
                    / net_sales
                )
                * 100,
                2,
            )
        )

    else:

        profit_margin = 0.0

    return {
        "total_sales":
            total_sales,

        "sales_return":
            sales_return,

        "net_sales":
            net_sales,

        "total_purchase":
            total_purchase,

        "purchase_return":
            purchase_return,

        "net_purchase":
            net_purchase,

        "cogs":
            net_cogs,

        "gross_profit":
            gross_profit,

        "operating_expense":
            operating_expense,

        "tailoring_expense":
            tailoring_expense,

        "total_expense":
            total_expense,

        "net_profit":
            net_profit,

        "profit_margin":
            profit_margin,

        "zero_cost_sale_items":
            zero_cost_items,
    }


# ==========================================================
# DAILY REPORT
# ==========================================================


def get_daily_report(
    db: Session,
    shop_id: int,
):
    today = date.today()

    # ------------------------------------------------------
    # SALES TODAY
    # ------------------------------------------------------

    sales = (
        db.query(Sale)
        .filter(
            Sale.shop_id == shop_id,
            func.date(
                Sale.created_at
            ) == today,
        )
        .all()
    )

    sale_ids = [
        sale.id
        for sale in sales
    ]

    total_sales = sum(
        (
            Decimal(
                str(
                    sale.total_amount
                    or 0
                )
            )
            for sale in sales
        ),
        Decimal("0.00"),
    )

    sales_return = get_sale_return_total(
        db=db,
        shop_id=shop_id,
        sale_ids=sale_ids,
    )

    net_sales = (
        total_sales
        - sales_return
    )

    # ------------------------------------------------------
    # COGS TODAY
    # ------------------------------------------------------

    total_cogs, zero_cost_items = (
        get_cogs_for_sales(
            db=db,
            shop_id=shop_id,
            sale_ids=sale_ids,
        )
    )

    returned_cogs = get_returned_cogs(
        db=db,
        shop_id=shop_id,
        sale_ids=sale_ids,
    )

    cogs = (
        total_cogs
        - returned_cogs
    )

    if cogs < 0:
        cogs = Decimal(
            "0.00"
        )

    # ------------------------------------------------------
    # PURCHASE TODAY
    # ------------------------------------------------------

    purchase = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        Purchase.grand_total
                    ),
                    0,
                )
            )
            .filter(
                Purchase.shop_id == shop_id,
                func.date(
                    Purchase.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    # ------------------------------------------------------
    # PURCHASE RETURN TODAY
    #
    # FIX:
    # Do NOT reference Purchase here.
    #
    # This query is against PurchaseReturn, so the shop
    # condition must use PurchaseReturn.shop_id.
    # ------------------------------------------------------

    purchase_return = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(
                        PurchaseReturn.total_amount
                    ),
                    0,
                )
            )
            .filter(
                PurchaseReturn.shop_id
                == shop_id,

                PurchaseReturn.status
                == "Completed",

                func.date(
                    PurchaseReturn.created_at
                ) == today,
            )
            .scalar()
            or 0
        )
    )

    net_purchase = (
        purchase
        - purchase_return
    )

    # ------------------------------------------------------
    # EXPENSE TODAY
    # ------------------------------------------------------

    operating_expense = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(Expense.amount),
                    0,
                )
            )
            .filter(
                Expense.shop_id == shop_id,
                func.date(Expense.created_at) == today,
            )
            .scalar()
            or 0
        )
    )

    tailoring_expense = get_tailoring_expense(
        db=db,
        shop_id=shop_id,
        report_date=today,
    )

    expense = (
        operating_expense
        + tailoring_expense
    )

    # ------------------------------------------------------
    # PROFIT TODAY
    # ------------------------------------------------------

    gross_profit = (
        net_sales
        - cogs
    )

    profit = (
        gross_profit
        - expense
    )

    return {
        "date":
            str(today),

        "sales":
            total_sales,

        "sales_return":
            sales_return,

        "net_sales":
            net_sales,

        "purchase":
            purchase,

        "purchase_return":
            purchase_return,

        "net_purchase":
            net_purchase,

        "cogs":
            cogs,

        "operating_expense":
            operating_expense,

        "tailoring_expense":
            tailoring_expense,

        "expense":
            expense,

        "gross_profit":
            gross_profit,

        "profit":
            profit,

        "zero_cost_sale_items":
            zero_cost_items,
    }


# ==========================================================
# MONTHLY REPORT
# ==========================================================


def get_monthly_report(
    db: Session,
    shop_id: int,
):
    months = (
        db.query(
            func.to_char(
                Sale.created_at,
                "YYYY-MM",
            ).label(
                "month"
            )
        )
        .filter(
            Sale.shop_id == shop_id,
        )
        .group_by(
            func.to_char(
                Sale.created_at,
                "YYYY-MM",
            )
        )
        .order_by(
            func.to_char(
                Sale.created_at,
                "YYYY-MM",
            )
        )
        .all()
    )

    report = []

    for month_row in months:

        month = month_row.month

        # --------------------------------------------------
        # SALES
        # --------------------------------------------------

        sales = (
            db.query(Sale)
            .filter(
                Sale.shop_id == shop_id,
                func.to_char(
                    Sale.created_at,
                    "YYYY-MM",
                ) == month,
            )
            .all()
        )

        sale_ids = [
            sale.id
            for sale in sales
        ]

        total_sales = sum(
            (
                Decimal(
                    str(
                        sale.total_amount
                        or 0
                    )
                )
                for sale in sales
            ),
            Decimal("0.00"),
        )

        sales_return = get_sale_return_total(
            db=db,
            shop_id=shop_id,
            sale_ids=sale_ids,
        )

        net_sales = (
            total_sales
            - sales_return
        )

        # --------------------------------------------------
        # COGS
        # --------------------------------------------------

        total_cogs, zero_cost_items = (
            get_cogs_for_sales(
                db=db,
                shop_id=shop_id,
                sale_ids=sale_ids,
            )
        )

        returned_cogs = get_returned_cogs(
            db=db,
            shop_id=shop_id,
            sale_ids=sale_ids,
        )

        cogs = (
            total_cogs
            - returned_cogs
        )

        if cogs < 0:
            cogs = Decimal(
                "0.00"
            )

        # --------------------------------------------------
        # PURCHASE
        # --------------------------------------------------

        purchase = Decimal(
            str(
                db.query(
                    func.coalesce(
                        func.sum(
                            Purchase.grand_total
                        ),
                        0,
                    )
                )
                .filter(
                    Purchase.shop_id == shop_id,
                    func.to_char(
                        Purchase.created_at,
                        "YYYY-MM",
                    ) == month,
                )
                .scalar()
                or 0
            )
        )

        # --------------------------------------------------
        # PURCHASE RETURN
        #
        # FIX:
        # Reference PurchaseReturn.shop_id only.
        # --------------------------------------------------

        purchase_return = Decimal(
            str(
                db.query(
                    func.coalesce(
                        func.sum(
                            PurchaseReturn.total_amount
                        ),
                        0,
                    )
                )
                .filter(
                    PurchaseReturn.shop_id
                    == shop_id,

                    PurchaseReturn.status
                    == "Completed",

                    func.to_char(
                        PurchaseReturn.created_at,
                        "YYYY-MM",
                    ) == month,
                )
                .scalar()
                or 0
            )
        )

        net_purchase = (
            purchase
            - purchase_return
        )

        # --------------------------------------------------
        # EXPENSE
        # --------------------------------------------------

        operating_expense = Decimal(
            str(
                db.query(
                    func.coalesce(
                        func.sum(Expense.amount),
                        0,
                    )
                )
                .filter(
                    Expense.shop_id == shop_id,
                    func.to_char(
                        Expense.created_at,
                        "YYYY-MM",
                    ) == month,
                )
                .scalar()
                or 0
            )
        )

        tailoring_expense = get_tailoring_expense(
            db=db,
            shop_id=shop_id,
            month=month,
        )

        expense = (
            operating_expense
            + tailoring_expense
        )

        # --------------------------------------------------
        # PROFIT
        # --------------------------------------------------

        gross_profit = (
            net_sales
            - cogs
        )

        profit = (
            gross_profit
            - expense
        )

        report.append(
            {
                "month":
                    month,

                "sales":
                    total_sales,

                "sales_return":
                    sales_return,

                "net_sales":
                    net_sales,

                "purchase":
                    purchase,

                "purchase_return":
                    purchase_return,

                "net_purchase":
                    net_purchase,

                "cogs":
                    cogs,

                "operating_expense":
                    operating_expense,

                "tailoring_expense":
                    tailoring_expense,

                "expense":
                    expense,

                "gross_profit":
                    gross_profit,

                "profit":
                    profit,

                "zero_cost_sale_items":
                    zero_cost_items,
            }
        )

    return report


# ==========================================================
# PRODUCT ANALYTICS
# ==========================================================


def get_product_analytics(
    db: Session,
    shop_id: int,
):
    """
    Return-aware product analytics.

    IMPORTANT:
    All active product variants are included, even if
    they have zero sales.

    This allows Analytics to detect:
    - unsold products with stock
    - total-stock shortages
    - K-stock shortages
    - R-stock shortages

    Return-aware fields:
    - units_sold
    - units_returned
    - net_units
    - gross_revenue
    - returned_revenue
    - net_revenue
    - cogs
    - net_cogs
    - gross_profit

    Stock configuration:
    - k_configured
    - r_configured
    - total_configured

    Stock status:
    - k_low
    - r_low
    - total_low
    - low_stock
    """

    # ======================================================
    # 1. ALL ACTIVE VARIANTS
    # ======================================================

    variant_rows = (
        db.query(
            Product.id.label(
                "product_id"
            ),

            Product.product_name.label(
                "product_name"
            ),

            ProductVariant.id.label(
                "variant_id"
            ),

            ProductVariant.sku.label(
                "sku"
            ),

            ProductVariant.size.label(
                "size"
            ),

            ProductVariant.color.label(
                "color"
            ),
        )
        .join(
            ProductVariant,
            ProductVariant.product_id
            == Product.id,
        )
        .filter(
            Product.shop_id == shop_id,
            Product.is_active == True,
            ProductVariant.is_active
            == True,
        )
        .all()
    )

    # ======================================================
    # 2. SALES BY VARIANT
    # ======================================================

    sales_rows = (
        db.query(
            SaleItem.variant_id.label(
                "variant_id"
            ),

            func.coalesce(
                func.sum(
                    SaleItem.quantity
                ),
                0,
            ).label(
                "units_sold"
            ),

            func.coalesce(
                func.sum(
                    SaleItem.total_price
                ),
                0,
            ).label(
                "gross_revenue"
            ),

            func.coalesce(
                func.sum(
                    SaleItem.cost_price
                    * SaleItem.quantity
                ),
                0,
            ).label(
                "cogs"
            ),
        )
        .select_from(
            SaleItem
        )
        .join(
            Sale,
            Sale.id
            == SaleItem.sale_id,
        )
        .filter(
            Sale.shop_id == shop_id,
            Sale.status == "Completed",
        )
        .group_by(
            SaleItem.variant_id,
        )
        .all()
    )

    sales_by_variant = {
        row.variant_id:
            row
        for row in sales_rows
    }

    # ======================================================
    # 3. RETURNED QUANTITY BY VARIANT
    # ======================================================

    return_quantity_rows = (
        db.query(
            SaleReturnItem.variant_id.label(
                "variant_id"
            ),

            func.coalesce(
                func.sum(
                    SaleReturnItem.quantity
                ),
                0,
            ).label(
                "units_returned"
            ),
        )
        .select_from(
            SaleReturnItem
        )
        .join(
            SaleReturn,
            SaleReturn.id
            == SaleReturnItem.sale_return_id,
        )
        .filter(
            SaleReturn.shop_id == shop_id,
            SaleReturn.status == "Completed",
        )
        .group_by(
            SaleReturnItem.variant_id,
        )
        .all()
    )

    returned_quantity_by_variant = {
        row.variant_id:
            int(
                row.units_returned
                or 0
            )
        for row in return_quantity_rows
    }

    # ======================================================
    # 4. RETURNED REVENUE BY VARIANT
    # ======================================================

    return_revenue_rows = (
        db.query(
            SaleReturnItem.variant_id.label(
                "variant_id"
            ),

            SaleItem.unit_price.label(
                "unit_price"
            ),

            func.coalesce(
                func.sum(
                    SaleReturnItem.quantity
                ),
                0,
            ).label(
                "returned_quantity"
            ),
        )
        .select_from(
            SaleReturnItem
        )
        .join(
            SaleReturn,
            SaleReturn.id
            == SaleReturnItem.sale_return_id,
        )
        .join(
            SaleItem,
            (
                SaleItem.sale_id
                == SaleReturn.sale_id
            )
            & (
                SaleItem.variant_id
                == SaleReturnItem.variant_id
            ),
        )
        .filter(
            SaleReturn.shop_id == shop_id,
            SaleReturn.status == "Completed",
        )
        .group_by(
            SaleReturnItem.variant_id,
            SaleItem.unit_price,
        )
        .all()
    )

    returned_revenue_by_variant = {}

    for row in return_revenue_rows:

        returned_quantity = int(
            row.returned_quantity
            or 0
        )

        unit_price = Decimal(
            str(
                row.unit_price
                or 0
            )
        )

        amount = (
            unit_price
            * Decimal(
                returned_quantity
            )
        )

        existing = (
            returned_revenue_by_variant.get(
                row.variant_id,
                Decimal("0.00"),
            )
        )

        returned_revenue_by_variant[
            row.variant_id
        ] = (
            existing
            + amount
        )

    # ======================================================
    # 5. BUILD ANALYTICS
    # ======================================================

    analytics = []

    for row in variant_rows:

        variant_id = row.variant_id

        sales_row = (
            sales_by_variant.get(
                variant_id
            )
        )

        if sales_row:

            units_sold = int(
                sales_row.units_sold
                or 0
            )

            gross_revenue = Decimal(
                str(
                    sales_row.gross_revenue
                    or 0
                )
            )

            cogs = Decimal(
                str(
                    sales_row.cogs
                    or 0
                )
            )

        else:

            units_sold = 0

            gross_revenue = (
                Decimal("0.00")
            )

            cogs = (
                Decimal("0.00")
            )

        # --------------------------------------------------
        # RETURNS
        # --------------------------------------------------

        units_returned = (
            returned_quantity_by_variant.get(
                variant_id,
                0,
            )
        )

        net_units = (
            units_sold
            - units_returned
        )

        if net_units < 0:
            net_units = 0

        returned_revenue = (
            returned_revenue_by_variant.get(
                variant_id,
                Decimal("0.00"),
            )
        )

        net_revenue = (
            gross_revenue
            - returned_revenue
        )

        if net_revenue < 0:
            net_revenue = (
                Decimal("0.00")
            )

        # --------------------------------------------------
        # AVERAGE HISTORICAL COST
        # --------------------------------------------------

        if units_sold > 0:

            average_cost = (
                cogs
                / Decimal(
                    units_sold
                )
            )

        else:

            average_cost = (
                Decimal("0.00")
            )

        returned_cogs = (
            average_cost
            * Decimal(
                units_returned
            )
        )

        net_cogs = (
            cogs
            - returned_cogs
        )

        if net_cogs < 0:
            net_cogs = (
                Decimal("0.00")
            )

        gross_profit = (
            net_revenue
            - net_cogs
        )

        # ==================================================
        # CURRENT STOCK
        # ==================================================

        stock = (
            db.query(Stock)
            .filter(
                Stock.variant_id
                == variant_id,
            )
            .first()
        )

        if stock:

            k_stock = int(
                stock.k_stock
                or 0
            )

            r_stock = int(
                stock.r_stock
                or 0
            )

            total_stock = (
                k_stock
                + r_stock
            )

            minimum_stock = int(
                stock.minimum_stock
                or 0
            )

            k_minimum_stock = int(
                stock.k_minimum_stock
                or 0
            )

            r_minimum_stock = int(
                stock.r_minimum_stock
                or 0
            )

        else:

            k_stock = 0
            r_stock = 0
            total_stock = 0

            minimum_stock = 0
            k_minimum_stock = 0
            r_minimum_stock = 0

        # ==================================================
        # CONFIGURATION
        # ==================================================

        k_configured = (
            k_minimum_stock > 0
        )

        r_configured = (
            r_minimum_stock > 0
        )

        total_configured = (
            minimum_stock > 0
        )

        # ==================================================
        # LOW STOCK
        # ==================================================

        k_low = (
            k_configured
            and k_stock
            <= k_minimum_stock
        )

        r_low = (
            r_configured
            and r_stock
            <= r_minimum_stock
        )

        total_low = (
            total_configured
            and total_stock
            <= minimum_stock
        )

        low_stock = (
            k_low
            or r_low
            or total_low
        )

        analytics.append(
            {
                "product_id":
                    row.product_id,

                "product_name":
                    row.product_name,

                "variant_id":
                    variant_id,

                "sku":
                    row.sku,

                "size":
                    row.size,

                "color":
                    row.color,

                "units_sold":
                    units_sold,

                "units_returned":
                    units_returned,

                "net_units":
                    net_units,

                "gross_revenue":
                    gross_revenue,

                "returned_revenue":
                    returned_revenue,

                "net_revenue":
                    net_revenue,

                "cogs":
                    cogs,

                "net_cogs":
                    net_cogs,

                "gross_profit":
                    gross_profit,

                "k_stock":
                    k_stock,

                "r_stock":
                    r_stock,

                "total_stock":
                    total_stock,

                "minimum_stock":
                    minimum_stock,

                "k_minimum_stock":
                    k_minimum_stock,

                "r_minimum_stock":
                    r_minimum_stock,

                "k_configured":
                    k_configured,

                "r_configured":
                    r_configured,

                "total_configured":
                    total_configured,

                "k_low":
                    k_low,

                "r_low":
                    r_low,

                "total_low":
                    total_low,

                "low_stock":
                    low_stock,
            }
        )

    # ======================================================
    # 6. RANKINGS
    # ======================================================

    ranked_products = [
        item
        for item in analytics
        if (
            item["units_sold"] > 0
            or item["net_revenue"] > 0
            or item["gross_profit"] > 0
        )
    ]

    ranked_products.sort(
        key=lambda item: (
            item["net_units"],
            item["net_revenue"],
        ),
        reverse=True,
    )

    if ranked_products:

        best_selling = max(
            ranked_products,
            key=lambda item:
                item["net_units"],
        )

        highest_revenue = max(
            ranked_products,
            key=lambda item:
                item["net_revenue"],
        )

        highest_profit = max(
            ranked_products,
            key=lambda item:
                item["gross_profit"],
        )

    else:

        best_selling = None
        highest_revenue = None
        highest_profit = None

    # ======================================================
    # 7. SLOW MOVING
    # ======================================================

    slow_moving = [
        item
        for item in analytics
        if (
            item["total_stock"] > 0
            and item["net_units"] <= 1
        )
    ]

    # ======================================================
    # 8. LOW STOCK
    # ======================================================

    low_stock_items = [
        item
        for item in analytics
        if item["low_stock"]
    ]

    # ======================================================
    # 9. SUMMARY
    # ======================================================

    total_units_sold = sum(
        item["net_units"]
        for item in analytics
    )

    total_revenue = sum(
        (
            Decimal(
                str(
                    item[
                        "net_revenue"
                    ]
                )
            )
            for item in analytics
        ),
        Decimal("0.00"),
    )

    total_returned_revenue = sum(
        (
            Decimal(
                str(
                    item[
                        "returned_revenue"
                    ]
                )
            )
            for item in analytics
        ),
        Decimal("0.00"),
    )

    total_cogs = sum(
        (
            Decimal(
                str(
                    item[
                        "net_cogs"
                    ]
                )
            )
            for item in analytics
        ),
        Decimal("0.00"),
    )

    total_gross_profit = sum(
        (
            Decimal(
                str(
                    item[
                        "gross_profit"
                    ]
                )
            )
            for item in analytics
        ),
        Decimal("0.00"),
    )

    return {
        "summary": {
            "total_variants":
                len(analytics),

            "total_units_sold":
                total_units_sold,

            "total_revenue":
                total_revenue,

            "total_returned_revenue":
                total_returned_revenue,

            "total_cogs":
                total_cogs,

            "total_gross_profit":
                total_gross_profit,

            "low_stock_variants":
                len(
                    low_stock_items
                ),

            "slow_moving_variants":
                len(
                    slow_moving
                ),
        },

        "best_selling":
            best_selling,

        "highest_revenue":
            highest_revenue,

        "highest_profit":
            highest_profit,

        "products":
            analytics,

        "slow_moving":
            sorted(
                slow_moving,
                key=lambda item: (
                    item["net_units"],
                    -item["total_stock"],
                ),
            ),

        "low_stock":
            sorted(
                low_stock_items,
                key=lambda item:
                    item["total_stock"],
            ),
    }