from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_db,
)

from app.dependencies import (
    get_current_user,
)

from app.models.supplier import (
    Supplier,
)

from app.crud.tailoring import (
    get_pending_tailoring_items,
    create_tailoring_job,
    get_tailoring_jobs,
    get_tailoring_job,
    update_tailoring_charge,
    update_tailoring_status,
    receive_tailoring_item,
    deliver_tailoring_item,
)

from app.schemas.supplier import (
    SupplierResponse,
)

from app.schemas.tailoring import (
    PendingTailoringItemResponse,
    TailoringJobCreate,
    TailoringJobDetailResponse,
    TailoringChargeUpdate,
    TailoringStatusUpdate,
    TailoringReceiveCreate,
    TailoringDeliveryCreate,
)


router = APIRouter(
    prefix="/tailoring",
    tags=["Tailoring"],
)


# ==========================================================
# GET AVAILABLE TAILORS
#
# Only TAILOR + BOTH suppliers appear.
# ==========================================================

@router.get(
    "/tailors",
    response_model=list[
        SupplierResponse
    ],
)
def available_tailors(
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        get_current_user
    ),
):

    return (
        db.query(
            Supplier
        )
        .filter(
            Supplier.shop_id
            == current_user.shop_id,

            Supplier.is_active
            == True,

            Supplier.supplier_type
            .in_(
                [
                    "TAILOR",
                    "BOTH",
                ]
            ),
        )
        .order_by(
            Supplier.supplier_name
        )
        .all()
    )


# ==========================================================
# PENDING ITEMS
# ==========================================================

@router.get(
    "/pending-items",
    response_model=list[
        PendingTailoringItemResponse
    ],
)
def pending_tailoring_items(
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        get_current_user
    ),
):

    return (
        get_pending_tailoring_items(
            db=db,

            shop_id=
                current_user.shop_id,
        )
    )


# ==========================================================
# ALL TAILORING JOBS
# ==========================================================

@router.get(
    "/jobs",
    response_model=list[
        TailoringJobDetailResponse
    ],
)
def tailoring_jobs(
    status: str | None = None,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    return get_tailoring_jobs(
        db=db,

        shop_id=
            current_user.shop_id,

        status=
            status,
    )


# ==========================================================
# ONE JOB
# ==========================================================

@router.get(
    "/jobs/{job_id}",
    response_model=
        TailoringJobDetailResponse,
)
def tailoring_job_details(
    job_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    return get_tailoring_job(
        db=db,

        shop_id=
            current_user.shop_id,

        job_id=
            job_id,
    )


# ==========================================================
# ASSIGN PENDING ITEM TO TAILOR
# ==========================================================

@router.post(
    "/jobs",
    response_model=
        TailoringJobDetailResponse,
)
def assign_tailoring_job(
    data: TailoringJobCreate,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    # ------------------------------------------------------
    # Explicitly verify this supplier is allowed
    # to perform tailoring.
    # ------------------------------------------------------

    tailor = (
        db.query(
            Supplier
        )
        .filter(
            Supplier.id
            == data.supplier_id,

            Supplier.shop_id
            == current_user.shop_id,

            Supplier.is_active
            == True,

            Supplier.supplier_type
            .in_(
                [
                    "TAILOR",
                    "BOTH",
                ]
            ),
        )
        .first()
    )

    if not tailor:

        raise HTTPException(
            status_code=400,
            detail=(
                "Selected supplier is not "
                "configured as a TAILOR "
                "or BOTH."
            ),
        )

    return create_tailoring_job(
        db=db,

        shop_id=
            current_user.shop_id,

        data=
            data,
    )


# ==========================================================
# UPDATE STITCHING CHARGE
# ==========================================================

@router.patch(
    "/jobs/{job_id}/charge",
    response_model=TailoringJobDetailResponse,
)
def change_stitching_charge(
    job_id: int,
    data: TailoringChargeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_tailoring_charge(
        db=db,
        shop_id=current_user.shop_id,
        job_id=job_id,
        data=data,
    )


# ==========================================================
# CHANGE JOB STATUS
# ==========================================================

@router.patch(
    "/jobs/{job_id}/status",
    response_model=
        TailoringJobDetailResponse,
)
def change_tailoring_status(
    job_id: int,

    data: TailoringStatusUpdate,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    return update_tailoring_status(
        db=db,

        shop_id=
            current_user.shop_id,

        job_id=
            job_id,

        data=
            data,
    )


# ==========================================================
# RECEIVE FINISHED ITEM FROM TAILOR
# ==========================================================

@router.post(
    "/jobs/{job_id}/receive",
    response_model=
        TailoringJobDetailResponse,
)
def receive_from_tailor(
    job_id: int,

    data: TailoringReceiveCreate,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    return receive_tailoring_item(
        db=db,

        shop_id=
            current_user.shop_id,

        job_id=
            job_id,

        data=
            data,
    )


# ==========================================================
# DELIVER RESERVED ITEM TO CUSTOMER
# ==========================================================

@router.post(
    "/jobs/{job_id}/deliver",
    response_model=
        TailoringJobDetailResponse,
)
def deliver_to_customer(
    job_id: int,

    data: TailoringDeliveryCreate,

    db: Session = Depends(
        get_db
    ),

    current_user=Depends(
        get_current_user
    ),
):

    return deliver_tailoring_item(
        db=db,

        shop_id=
            current_user.shop_id,

        job_id=
            job_id,

        data=
            data,
    )