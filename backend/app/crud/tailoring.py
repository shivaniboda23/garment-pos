from datetime import (
    datetime,
    timezone,
)

from decimal import Decimal

from fastapi import HTTPException

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.models.sale_item import SaleItem
from app.models.supplier import Supplier
from app.models.tailoring_job import TailoringJob
from app.models.tailor_payment import TailorPayment

from app.schemas.tailoring import (
    TailoringJobCreate,
    TailoringChargeUpdate,
    TailoringStatusUpdate,
    TailoringReceiveCreate,
    TailoringDeliveryCreate,
)

from app.services.billing import (
    resolve_bill_status,
)


# ==========================================================
# HELPERS
# ==========================================================


def _generate_job_number(
    shop_id: int,
):
    """
    Generate unique tailoring job number.

    Example:
    TJ-3-20260824160530123456
    """

    now = datetime.now(
        timezone.utc
    )

    return (
        f"TJ-{shop_id}-"
        f"{now.strftime('%Y%m%d%H%M%S%f')}"
    )


# ==========================================================
# PRODUCT NAME HELPER
# ==========================================================


def _product_name(
    variant,
):
    """
    Safely extract product name from variant.

    Historical data may have incomplete relationships,
    so this helper never crashes the tailoring API.
    """

    if not variant:
        return ""

    try:

        product = variant.product

        if not product:
            return ""

        return str(
            getattr(
                product,
                "product_name",
                "",
            )
            or ""
        )

    except Exception:

        return ""


# ==========================================================
# PENDING K / R HELPER
# ==========================================================


def _get_pending_bucket(
    bill_item: BillItem,
    stock_type: str,
):
    """
    Calculate pending quantity for a particular K/R bucket.

    BillItem stores:

        k_quantity
            = total K ordered

        k_delivered_qty
            = K already delivered

    Therefore:

        pending K
            = k_quantity - k_delivered_qty

    Same logic for R.
    """

    stock_type = (
        str(
            stock_type
        )
        .strip()
        .upper()
    )

    if stock_type == "K":

        ordered = int(
            bill_item.k_quantity
            or 0
        )

        delivered = int(
            bill_item.k_delivered_qty
            or 0
        )

    elif stock_type == "R":

        ordered = int(
            bill_item.r_quantity
            or 0
        )

        delivered = int(
            bill_item.r_delivered_qty
            or 0
        )

    else:

        return 0

    return max(
        0,
        ordered - delivered,
    )


# ==========================================================
# ACTIVE ASSIGNED QUANTITY
# ==========================================================


def _active_assigned_quantity(
    db: Session,
    shop_id: int,
    bill_item_id: int,
    stock_type: str,
):
    """
    Determine how much of the currently pending quantity
    has already been assigned to tailoring jobs.

    Delivered and Cancelled jobs are not counted as active
    tailoring allocations.
    """

    stock_type = (
        str(
            stock_type
        )
        .strip()
        .upper()
    )

    jobs = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.shop_id
            == shop_id,

            TailoringJob.bill_item_id
            == bill_item_id,

            TailoringJob.stock_type
            == stock_type,

            TailoringJob.status
            != "Cancelled",

            TailoringJob.status
            != "Delivered",
        )
        .all()
    )

    total = 0

    for job in jobs:

        assigned_quantity = int(
            job.quantity
            or 0
        )

        delivered_quantity = int(
            job.delivered_quantity
            or 0
        )

        remaining = (
            assigned_quantity
            - delivered_quantity
        )

        if remaining > 0:
            total += remaining

    return total


# ==========================================================
# JOB DETAIL RESPONSE HELPER
# ==========================================================


def _job_detail(
    job: TailoringJob,
):
    """
    Convert TailoringJob into the detailed API structure
    expected by TailoringJobDetailResponse.
    """

    customer = (
        job.customer
        if job
        else None
    )

    supplier = (
        job.supplier
        if job
        else None
    )

    variant = (
        job.variant
        if job
        else None
    )

    bill = (
        job.bill
        if job
        else None
    )

    quantity = int(
        job.quantity
        or 0
    )

    received = int(
        job.received_quantity
        or 0
    )

    delivered = int(
        job.delivered_quantity
        or 0
    )

    # ------------------------------------------------------
    # Ready quantity:
    #
    # Returned by tailor
    # -
    # already handed to customer
    # ------------------------------------------------------

    ready_quantity = max(
        0,
        received - delivered,
    )

    # ------------------------------------------------------
    # Still with tailor / not yet received.
    # ------------------------------------------------------

    remaining_at_tailor = max(
        0,
        quantity - received,
    )

    # ------------------------------------------------------
    # Still not handed to customer.
    # ------------------------------------------------------

    remaining_to_customer = max(
        0,
        quantity - delivered,
    )

    stitching_charge = Decimal(
        str(
            job.stitching_charge
            or 0
        )
    )

    tailor_paid_amount = sum(
        (
            Decimal(
                str(
                    payment.amount
                    or 0
                )
            )
            for payment in (
                job.tailor_payments
                or []
            )
        ),
        Decimal("0.00"),
    )

    tailor_due_amount = max(
        Decimal("0.00"),
        stitching_charge
        - tailor_paid_amount,
    )

    if stitching_charge <= 0:
        tailor_payment_status = "No Charge"
    elif tailor_paid_amount <= 0:
        tailor_payment_status = "Unpaid"
    elif tailor_due_amount <= 0:
        tailor_payment_status = "Paid"
    else:
        tailor_payment_status = "Partial"

    return {
        "id":
            job.id,

        "job_number":
            job.job_number,

        "shop_id":
            job.shop_id,

        "bill_id":
            job.bill_id,

        "bill_item_id":
            job.bill_item_id,

        "sale_item_id":
            job.sale_item_id,

        "customer_id":
            job.customer_id,

        "supplier_id":
            job.supplier_id,

        "variant_id":
            job.variant_id,

        "stock_type":
            job.stock_type,

        "quantity":
            quantity,

        "received_quantity":
            received,

        "delivered_quantity":
            delivered,

        "status":
            job.status,

        "stitching_charge":
            job.stitching_charge,

        "expected_date":
            job.expected_date,

        "assigned_at":
            job.assigned_at,

        "stitching_started_at":
            job.stitching_started_at,

        "received_at":
            job.received_at,

        "customer_notified_at":
            job.customer_notified_at,

        "delivered_at":
            job.delivered_at,

        "instructions":
            job.instructions,

        "notes":
            job.notes,

        "created_at":
            job.created_at,

        "updated_at":
            job.updated_at,

        "invoice_number":
            (
                bill.invoice_number
                if bill
                else ""
            ),

        "customer_name":
            (
                customer.customer_name
                if customer
                else ""
            ),

        "customer_phone":
            (
                getattr(
                    customer,
                    "phone",
                    None,
                )
                if customer
                else None
            ),

        "supplier_name":
            (
                supplier.supplier_name
                if supplier
                else ""
            ),

        "product_name":
            _product_name(
                variant
            ),

        "sku":
            (
                variant.sku
                if variant
                and variant.sku
                else ""
            ),

        "size":
            (
                getattr(
                    variant,
                    "size",
                    None,
                )
                if variant
                else None
            ),

        "color":
            (
                getattr(
                    variant,
                    "color",
                    None,
                )
                if variant
                else None
            ),

        "ready_quantity":
            ready_quantity,

        "remaining_at_tailor":
            remaining_at_tailor,

        "remaining_to_customer":
            remaining_to_customer,

        "tailor_paid_amount":
            tailor_paid_amount,

        "tailor_due_amount":
            tailor_due_amount,

        "tailor_payment_status":
            tailor_payment_status,
    }


# ==========================================================
# GET PENDING BILL ITEMS
# ==========================================================


def get_pending_tailoring_items(
    db: Session,
    shop_id: int,
):
    """
    Return current actionable pending customer items.

    IMPORTANT:

    Older legacy BillItems exist in this database where:

        variant_id = NULL

    Example old Ravi Kumar bills.

    Those historical records cannot participate in the
    modern:

        Product
            -> Variant
            -> K/R
            -> Tailoring

    workflow.

    We therefore ignore structurally invalid legacy rows here.

    We DO NOT:
        - delete them
        - mark them delivered
        - alter accounting
        - change their bill history

    They remain preserved for later legacy-data cleanup.
    """

    rows = (
        db.query(
            BillItem
        )
        .join(
            Bill,
            Bill.id
            == BillItem.bill_id,
        )
        .filter(
            Bill.shop_id
            == shop_id,

            BillItem.pending_qty
            > 0,

            # ----------------------------------------------
            # Legacy BillItems with NULL variants are not
            # actionable under the current ERP architecture.
            # ----------------------------------------------

            BillItem.variant_id
            .isnot(None),
        )
        .order_by(
            Bill.created_at.asc(),
            BillItem.id.asc(),
        )
        .all()
    )

    result = []

    for item in rows:

        bill = item.bill

        # --------------------------------------------------
        # Safety:
        # Bill relationship must exist.
        # --------------------------------------------------

        if not bill:
            continue

        # --------------------------------------------------
        # Pending fulfillment must belong to a customer.
        # --------------------------------------------------

        customer = bill.customer

        if not customer:
            continue

        # --------------------------------------------------
        # Variant must still exist.
        #
        # variant_id may theoretically contain a historical
        # broken FK from older data.
        # --------------------------------------------------

        variant = item.variant

        if not variant:
            continue

        # --------------------------------------------------
        # Calculate actual K/R pending quantities.
        # --------------------------------------------------

        pending_k = (
            _get_pending_bucket(
                bill_item=item,
                stock_type="K",
            )
        )

        pending_r = (
            _get_pending_bucket(
                bill_item=item,
                stock_type="R",
            )
        )

        # --------------------------------------------------
        # If BillItem says pending_qty > 0 but neither K nor R
        # has pending quantity, it is structurally invalid
        # legacy data.
        #
        # Do not crash / do not fake a stock type.
        # --------------------------------------------------

        if (
            pending_k <= 0
            and pending_r <= 0
        ):
            continue

        # --------------------------------------------------
        # How much pending K has already been assigned?
        # --------------------------------------------------

        assigned_k = (
            _active_assigned_quantity(
                db=db,
                shop_id=shop_id,
                bill_item_id=item.id,
                stock_type="K",
            )
        )

        # --------------------------------------------------
        # How much pending R has already been assigned?
        # --------------------------------------------------

        assigned_r = (
            _active_assigned_quantity(
                db=db,
                shop_id=shop_id,
                bill_item_id=item.id,
                stock_type="R",
            )
        )

        # --------------------------------------------------
        # Remaining quantity that may still be assigned.
        # --------------------------------------------------

        available_k = max(
            0,
            pending_k
            - assigned_k,
        )

        available_r = max(
            0,
            pending_r
            - assigned_r,
        )

        result.append(
            {
                "bill_id":
                    bill.id,

                "bill_item_id":
                    item.id,

                "invoice_number":
                    bill.invoice_number,

                "customer_id":
                    customer.id,

                "customer_name":
                    customer.customer_name,

                "customer_phone":
                    getattr(
                        customer,
                        "phone",
                        None,
                    ),

                "variant_id":
                    item.variant_id,

                "product_name":
                    _product_name(
                        variant
                    ),

                "sku":
                    (
                        variant.sku
                        or ""
                    ),

                "size":
                    getattr(
                        variant,
                        "size",
                        None,
                    ),

                "color":
                    getattr(
                        variant,
                        "color",
                        None,
                    ),

                "ordered_qty":
                    int(
                        item.ordered_qty
                        or 0
                    ),

                "delivered_qty":
                    int(
                        item.delivered_qty
                        or 0
                    ),

                "pending_qty":
                    int(
                        item.pending_qty
                        or 0
                    ),

                "pending_k":
                    pending_k,

                "pending_r":
                    pending_r,

                "assigned_k":
                    assigned_k,

                "assigned_r":
                    assigned_r,

                "available_to_assign_k":
                    available_k,

                "available_to_assign_r":
                    available_r,

                "item_status":
                    item.item_status,
            }
        )

    return result


# ==========================================================
# CREATE TAILORING JOB
# ==========================================================


def create_tailoring_job(
    db: Session,
    shop_id: int,
    data: TailoringJobCreate,
):
    """
    Assign part or all of a pending BillItem to a tailor.

    This does NOT modify physical shop stock.

    Tailoring output is reserved specifically for the
    associated customer/bill.
    """

    stock_type = (
        data.stock_type
        .strip()
        .upper()
    )

    # ======================================================
    # BILL ITEM
    # ======================================================

    bill_item = (
        db.query(
            BillItem
        )
        .join(
            Bill,
            Bill.id
            == BillItem.bill_id,
        )
        .filter(
            BillItem.id
            == data.bill_item_id,

            Bill.shop_id
            == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not bill_item:

        raise HTTPException(
            status_code=404,
            detail=(
                "Bill item not found."
            ),
        )

    # ======================================================
    # BILL
    # ======================================================

    bill = (
        db.query(
            Bill
        )
        .filter(
            Bill.id
            == bill_item.bill_id,

            Bill.shop_id
            == shop_id,
        )
        .first()
    )

    if not bill:

        raise HTTPException(
            status_code=404,
            detail=(
                "Bill not found."
            ),
        )

    # ======================================================
    # CUSTOMER REQUIRED
    # ======================================================

    if bill.customer_id is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Pending tailoring requires "
                "a customer-linked bill."
            ),
        )

    # ======================================================
    # VALID VARIANT REQUIRED
    # ======================================================

    if bill_item.variant_id is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "This is a legacy pending item "
                "without a product variant and "
                "cannot be assigned to tailoring."
            ),
        )

    if not bill_item.variant:

        raise HTTPException(
            status_code=400,
            detail=(
                "The linked product variant "
                "does not exist."
            ),
        )

    # ======================================================
    # SUPPLIER / TAILOR
    # ======================================================

    supplier = (
        db.query(
            Supplier
        )
        .filter(
            Supplier.id
            == data.supplier_id,

            Supplier.shop_id
            == shop_id,

            Supplier.is_active
            .is_(True),
        )
        .first()
    )

    if not supplier:

        raise HTTPException(
            status_code=404,
            detail=(
                "Selected tailor/supplier "
                "was not found."
            ),
        )

    # ------------------------------------------------------
    # Only TAILOR or BOTH can receive tailoring jobs.
    # ------------------------------------------------------

    supplier_type = (
        str(
            getattr(
                supplier,
                "supplier_type",
                "SUPPLIER",
            )
            or "SUPPLIER"
        )
        .strip()
        .upper()
    )

    if supplier_type not in (
        "TAILOR",
        "BOTH",
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Selected supplier is not "
                "configured as a TAILOR "
                "or BOTH."
            ),
        )

    # ======================================================
    # PENDING QUANTITY
    # ======================================================

    pending_bucket = (
        _get_pending_bucket(
            bill_item=bill_item,
            stock_type=stock_type,
        )
    )

    if pending_bucket <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                f"No pending {stock_type} "
                f"quantity exists for "
                f"this bill item."
            ),
        )

    # ======================================================
    # ALREADY ASSIGNED
    # ======================================================

    assigned = (
        _active_assigned_quantity(
            db=db,
            shop_id=shop_id,
            bill_item_id=bill_item.id,
            stock_type=stock_type,
        )
    )

    available_to_assign = max(
        0,
        pending_bucket
        - assigned,
    )

    if data.quantity > available_to_assign:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    (
                        "Tailoring quantity exceeds "
                        "unassigned pending quantity."
                    ),

                "stock_type":
                    stock_type,

                "pending_quantity":
                    pending_bucket,

                "already_assigned":
                    assigned,

                "available_to_assign":
                    available_to_assign,
            },
        )

    # ======================================================
    # SALE ITEM
    # ======================================================

    sale_item = (
        db.query(
            SaleItem
        )
        .filter(
            SaleItem.sale_id
            == bill.sale_id,

            SaleItem.variant_id
            == bill_item.variant_id,
        )
        .first()
    )

    if not sale_item:

        raise HTTPException(
            status_code=404,
            detail=(
                "Linked sale item "
                "was not found."
            ),
        )

    # ======================================================
    # JOB NUMBER
    # ======================================================

    job_number = (
        _generate_job_number(
            shop_id
        )
    )

    while (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.job_number
            == job_number
        )
        .first()
    ):

        job_number = (
            _generate_job_number(
                shop_id
            )
        )

    # ======================================================
    # CREATE
    # ======================================================

    try:

        job = TailoringJob(

            shop_id=
                shop_id,

            job_number=
                job_number,

            bill_id=
                bill.id,

            bill_item_id=
                bill_item.id,

            sale_item_id=
                sale_item.id,

            customer_id=
                bill.customer_id,

            supplier_id=
                supplier.id,

            variant_id=
                bill_item.variant_id,

            stock_type=
                stock_type,

            quantity=
                int(
                    data.quantity
                ),

            received_quantity=
                0,

            delivered_quantity=
                0,

            status=
                "Assigned",

            stitching_charge=
                Decimal(
                    str(
                        data.stitching_charge
                        or 0
                    )
                ),

            expected_date=
                data.expected_date,

            instructions=
                data.instructions,

            notes=
                data.notes,
        )

        db.add(
            job
        )

        db.commit()

        db.refresh(
            job
        )

        return _job_detail(
            job
        )

    except HTTPException:

        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Tailoring job creation "
                f"failed: {str(exc)}"
            ),
        )


# ==========================================================
# GET ALL TAILORING JOBS
# ==========================================================


def get_tailoring_jobs(
    db: Session,
    shop_id: int,
    status: str | None = None,
):

    query = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.shop_id
            == shop_id
        )
    )

    if status:

        query = query.filter(
            TailoringJob.status
            == status
        )

    jobs = (
        query
        .order_by(
            TailoringJob.created_at
            .desc(),

            TailoringJob.id
            .desc(),
        )
        .all()
    )

    return [
        _job_detail(
            job
        )
        for job in jobs
    ]


# ==========================================================
# GET ONE TAILORING JOB
# ==========================================================


def get_tailoring_job(
    db: Session,
    shop_id: int,
    job_id: int,
):

    job = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.id
            == job_id,

            TailoringJob.shop_id
            == shop_id,
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail=(
                "Tailoring job not found."
            ),
        )

    return _job_detail(
        job
    )


# ==========================================================
# UPDATE STITCHING CHARGE
# ==========================================================


def update_tailoring_charge(
    db: Session,
    shop_id: int,
    job_id: int,
    data: TailoringChargeUpdate,
):
    job = (
        db.query(TailoringJob)
        .filter(
            TailoringJob.id == job_id,
            TailoringJob.shop_id == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tailoring job not found.",
        )

    if job.status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled tailoring job charge cannot be changed.",
        )

    new_charge = Decimal(
        str(
            data.stitching_charge
            or 0
        )
    )

    paid_amount = Decimal(
        str(
            db.query(
                func.coalesce(
                    func.sum(TailorPayment.amount),
                    0,
                )
            )
            .filter(
                TailorPayment.shop_id == shop_id,
                TailorPayment.tailoring_job_id == job.id,
            )
            .scalar()
            or 0
        )
    )

    if new_charge < paid_amount:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Stitching charge ₹{new_charge} cannot be lower "
                f"than already paid amount ₹{paid_amount}."
            ),
        )

    try:
        job.stitching_charge = new_charge
        db.commit()
        db.refresh(job)
        return _job_detail(job)

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Tailoring charge update "
                f"failed: {str(exc)}"
            ),
        )


# ==========================================================
# UPDATE TAILORING STATUS
# ==========================================================


def update_tailoring_status(
    db: Session,
    shop_id: int,
    job_id: int,
    data: TailoringStatusUpdate,
):

    job = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.id
            == job_id,

            TailoringJob.shop_id
            == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail=(
                "Tailoring job not found."
            ),
        )

    new_status = (
        data.status
        .strip()
    )

    # ------------------------------------------------------
    # Final states cannot be changed.
    # ------------------------------------------------------

    if job.status in (
        "Delivered",
        "Cancelled",
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"{job.status} job "
                "cannot be changed."
            ),
        )

    now = datetime.now(
        timezone.utc
    )

    # ======================================================
    # ASSIGNED
    # ======================================================

    if new_status == "Assigned":

        if job.status != "Assigned":

            raise HTTPException(
                status_code=400,
                detail=(
                    "Job cannot be moved "
                    "back to Assigned."
                ),
            )

    # ======================================================
    # IN STITCHING
    # ======================================================

    elif (
        new_status
        == "In Stitching"
    ):

        if job.status not in (
            "Assigned",
            "In Stitching",
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only an Assigned job "
                    "can be moved to "
                    "In Stitching."
                ),
            )

        job.status = (
            "In Stitching"
        )

        if (
            job.stitching_started_at
            is None
        ):

            job.stitching_started_at = (
                now
            )

    # ======================================================
    # CUSTOMER NOTIFIED
    # ======================================================

    elif (
        new_status
        == "Customer Notified"
    ):

        ready_quantity = (
            int(
                job.received_quantity
                or 0
            )
            - int(
                job.delivered_quantity
                or 0
            )
        )

        if ready_quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No received item is "
                    "ready for customer."
                ),
            )

        if job.status not in (
            "Ready",
            "Partially Ready",
            "Customer Notified",
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Job must have a ready "
                    "item before notifying "
                    "the customer."
                ),
            )

        job.status = (
            "Customer Notified"
        )

        job.customer_notified_at = (
            now
        )

    # ======================================================
    # CANCEL
    # ======================================================

    elif (
        new_status
        == "Cancelled"
    ):

        tailor_paid_amount = (
            db.query(
                func.coalesce(
                    func.sum(TailorPayment.amount),
                    0,
                )
            )
            .filter(
                TailorPayment.shop_id == shop_id,
                TailorPayment.tailoring_job_id == job.id,
            )
            .scalar()
            or 0
        )

        if Decimal(str(tailor_paid_amount)) > 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A tailoring job with recorded tailor payments "
                    "cannot be cancelled."
                ),
            )

        if (
            int(
                job.received_quantity
                or 0
            )
            > 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "A tailoring job with "
                    "received items cannot "
                    "be cancelled."
                ),
            )

        if (
            int(
                job.delivered_quantity
                or 0
            )
            > 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "A delivered tailoring "
                    "job cannot be cancelled."
                ),
            )

        job.status = (
            "Cancelled"
        )

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid tailoring status."
            ),
        )

    try:

        db.commit()

        db.refresh(
            job
        )

        return _job_detail(
            job
        )

    except HTTPException:

        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Tailoring status update "
                f"failed: {str(exc)}"
            ),
        )


# ==========================================================
# RECEIVE ITEM FROM TAILOR
# ==========================================================


def receive_tailoring_item(
    db: Session,
    shop_id: int,
    job_id: int,
    data: TailoringReceiveCreate,
):
    """
    Tailor returns completed merchandise.

    IMPORTANT:

    Returned tailored merchandise is RESERVED stock for
    this customer.

    It is NOT added to normal Stock.k_stock/r_stock.
    """

    job = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.id
            == job_id,

            TailoringJob.shop_id
            == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail=(
                "Tailoring job not found."
            ),
        )

    if job.status in (
        "Delivered",
        "Cancelled",
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot receive items "
                f"for a {job.status} job."
            ),
        )

    quantity = int(
        data.quantity
    )

    current_received = int(
        job.received_quantity
        or 0
    )

    total_quantity = int(
        job.quantity
        or 0
    )

    remaining = (
        total_quantity
        - current_received
    )

    if remaining <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "All tailoring items "
                "have already been received."
            ),
        )

    if quantity > remaining:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    (
                        "Received quantity exceeds "
                        "remaining tailoring quantity."
                    ),

                "job_quantity":
                    total_quantity,

                "already_received":
                    current_received,

                "remaining":
                    remaining,
            },
        )

    new_received = (
        current_received
        + quantity
    )

    job.received_quantity = (
        new_received
    )

    if job.received_at is None:
        job.received_at = (
            datetime.now(
                timezone.utc
            )
        )

    # ------------------------------------------------------
    # Full tailoring quantity returned.
    # ------------------------------------------------------

    if (
        new_received
        == total_quantity
    ):

        job.status = (
            "Ready"
        )

    else:

        job.status = (
            "Partially Ready"
        )

    if data.notes:

        job.notes = (
            data.notes
        )

    try:

        db.commit()

        db.refresh(
            job
        )

        return _job_detail(
            job
        )

    except HTTPException:

        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Tailoring receiving "
                f"failed: {str(exc)}"
            ),
        )


# ==========================================================
# DELIVER RESERVED ITEM TO CUSTOMER
# ==========================================================


def deliver_tailoring_item(
    db: Session,
    shop_id: int,
    job_id: int,
    data: TailoringDeliveryCreate,
):
    """
    Deliver a finished reserved tailoring item to customer.

    This updates:

        TailoringJob
        BillItem
        SaleItem
        Bill delivery status

    It does NOT deduct normal shop stock because this item
    was never placed into normal available inventory.
    """

    # ======================================================
    # JOB
    # ======================================================

    job = (
        db.query(
            TailoringJob
        )
        .filter(
            TailoringJob.id
            == job_id,

            TailoringJob.shop_id
            == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail=(
                "Tailoring job not found."
            ),
        )

    if job.status in (
        "Assigned",
        "In Stitching",
        "Cancelled",
        "Delivered",
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "This tailoring job "
                "does not currently have "
                "an item ready for delivery."
            ),
        )

    quantity = int(
        data.quantity
    )

    # ======================================================
    # READY QUANTITY
    # ======================================================

    ready_quantity = (
        int(
            job.received_quantity
            or 0
        )
        - int(
            job.delivered_quantity
            or 0
        )
    )

    if ready_quantity <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "No tailoring item is "
                "currently ready for delivery."
            ),
        )

    if quantity > ready_quantity:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    (
                        "Delivery quantity exceeds "
                        "ready quantity."
                    ),

                "ready_quantity":
                    ready_quantity,
            },
        )

    # ======================================================
    # BILL ITEM
    # ======================================================

    bill_item = (
        db.query(
            BillItem
        )
        .filter(
            BillItem.id
            == job.bill_item_id,
        )
        .with_for_update()
        .first()
    )

    if not bill_item:

        raise HTTPException(
            status_code=404,
            detail=(
                "Linked bill item "
                "was not found."
            ),
        )

    # ======================================================
    # BILL
    # ======================================================

    bill = (
        db.query(
            Bill
        )
        .filter(
            Bill.id
            == job.bill_id,

            Bill.shop_id
            == shop_id,
        )
        .with_for_update()
        .first()
    )

    if not bill:

        raise HTTPException(
            status_code=404,
            detail=(
                "Linked bill "
                "was not found."
            ),
        )

    # ======================================================
    # SALE ITEM
    # ======================================================

    sale_item = (
        db.query(
            SaleItem
        )
        .filter(
            SaleItem.id
            == job.sale_item_id,
        )
        .with_for_update()
        .first()
    )

    if not sale_item:

        raise HTTPException(
            status_code=404,
            detail=(
                "Linked sale item "
                "was not found."
            ),
        )

    # ======================================================
    # CURRENT PENDING K/R
    # ======================================================

    pending_bucket = (
        _get_pending_bucket(
            bill_item=bill_item,
            stock_type=job.stock_type,
        )
    )

    if pending_bucket <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                f"No pending "
                f"{job.stock_type} "
                f"quantity remains "
                f"on this bill item."
            ),
        )

    if quantity > pending_bucket:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    (
                        "Delivery exceeds current "
                        "pending bill quantity."
                    ),

                "stock_type":
                    job.stock_type,

                "pending_quantity":
                    pending_bucket,
            },
        )

    current_bill_pending = int(
        bill_item.pending_qty
        or 0
    )

    if quantity > current_bill_pending:

        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery exceeds total "
                "pending bill quantity."
            ),
        )

    # ======================================================
    # BILL ITEM FULFILLMENT
    # ======================================================

    bill_item.delivered_qty = (
        int(
            bill_item.delivered_qty
            or 0
        )
        + quantity
    )

    bill_item.pending_qty = (
        current_bill_pending
        - quantity
    )

    # ------------------------------------------------------
    # K DELIVERY
    # ------------------------------------------------------

    if job.stock_type == "K":

        bill_item.k_delivered_qty = (
            int(
                bill_item.k_delivered_qty
                or 0
            )
            + quantity
        )

    # ------------------------------------------------------
    # R DELIVERY
    # ------------------------------------------------------

    elif job.stock_type == "R":

        bill_item.r_delivered_qty = (
            int(
                bill_item.r_delivered_qty
                or 0
            )
            + quantity
        )

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid tailoring stock type."
            ),
        )

    # ======================================================
    # BILL ITEM STATUS
    # ======================================================

    if (
        int(
            bill_item.pending_qty
            or 0
        )
        <= 0
    ):

        bill_item.pending_qty = 0

        bill_item.item_status = (
            "Delivered"
        )

    else:

        bill_item.item_status = (
            "Partially Delivered"
        )

    # ======================================================
    # SALE ITEM / COGS FULFILLMENT
    #
    # Example:
    #
    # Before tailoring delivery:
    #
    # quantity = 4
    # K        = 4
    #
    # Deliver pending 1 K:
    #
    # quantity = 5
    # K        = 5
    #
    # COGS now recognizes that additional fulfilled piece.
    # ======================================================

    sale_item.quantity = (
        int(
            sale_item.quantity
            or 0
        )
        + quantity
    )

    if job.stock_type == "K":

        sale_item.k_quantity = (
            int(
                sale_item.k_quantity
                or 0
            )
            + quantity
        )

    else:

        sale_item.r_quantity = (
            int(
                sale_item.r_quantity
                or 0
            )
            + quantity
        )

    # ======================================================
    # TAILORING JOB DELIVERY
    # ======================================================

    job.delivered_quantity = (
        int(
            job.delivered_quantity
            or 0
        )
        + quantity
    )

    now = datetime.now(
        timezone.utc
    )

    # ------------------------------------------------------
    # Entire tailoring job delivered.
    # ------------------------------------------------------

    if (
        int(
            job.delivered_quantity
            or 0
        )
        >= int(
            job.quantity
            or 0
        )
    ):

        job.delivered_quantity = (
            int(
                job.quantity
                or 0
            )
        )

        job.status = (
            "Delivered"
        )

        job.delivered_at = (
            now
        )

    else:

        # --------------------------------------------------
        # Some tailoring quantity remains.
        # --------------------------------------------------

        remaining_ready = (
            int(
                job.received_quantity
                or 0
            )
            - int(
                job.delivered_quantity
                or 0
            )
        )

        if remaining_ready > 0:

            job.status = (
                "Ready"
            )

        else:

            job.status = (
                "In Stitching"
            )

    if data.notes:

        job.notes = (
            data.notes
        )

    # ======================================================
    # FLUSH CHANGES
    #
    # Important before checking whether the entire bill
    # still contains pending BillItems.
    # ======================================================

    db.flush()

    # ======================================================
    # CHECK WHOLE BILL
    # ======================================================

    remaining_bill_items = (
        db.query(
            func.count(
                BillItem.id
            )
        )
        .filter(
            BillItem.bill_id
            == bill.id,

            BillItem.pending_qty
            > 0,
        )
        .scalar()
        or 0
    )

    # ------------------------------------------------------
    # Payment status remains separate.
    #
    # A bill can be:
    #
    # payment_status = Partial
    # bill_status    = Completed
    #
    # meaning all products were delivered but payment
    # is still due.
    # ------------------------------------------------------

    bill.bill_status = (
        resolve_bill_status(
            remaining_bill_items
            > 0
        )
    )

    # ======================================================
    # COMMIT
    # ======================================================

    try:

        db.commit()

        db.refresh(
            job
        )

        return _job_detail(
            job
        )

    except HTTPException:

        db.rollback()
        raise

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Tailoring delivery "
                f"failed: {str(exc)}"
            ),
        )