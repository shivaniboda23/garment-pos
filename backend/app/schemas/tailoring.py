from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)


# ==========================================================
# CREATE JOB
# ==========================================================

class TailoringJobCreate(BaseModel):

    bill_item_id: int

    supplier_id: int

    stock_type: str

    quantity: int

    expected_date: Optional[
        datetime
    ] = None

    stitching_charge: Decimal = Decimal(
        "0.00"
    )

    instructions: Optional[
        str
    ] = None

    notes: Optional[
        str
    ] = None

    @field_validator(
        "stock_type"
    )
    @classmethod
    def validate_stock_type(
        cls,
        value,
    ):
        value = (
            value
            .strip()
            .upper()
        )

        if value not in (
            "K",
            "R",
        ):
            raise ValueError(
                "Stock type must be K or R."
            )

        return value

    @field_validator(
        "quantity"
    )
    @classmethod
    def validate_quantity(
        cls,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        return value

    @field_validator(
        "stitching_charge"
    )
    @classmethod
    def validate_charge(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Stitching charge cannot be negative."
            )

        return value


# ==========================================================
# UPDATE STITCHING CHARGE
# ==========================================================

class TailoringChargeUpdate(BaseModel):

    stitching_charge: Decimal

    @field_validator(
        "stitching_charge"
    )
    @classmethod
    def validate_charge(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Stitching charge cannot be negative."
            )

        return value


# ==========================================================
# STATUS
# ==========================================================

class TailoringStatusUpdate(BaseModel):

    status: str

    @field_validator(
        "status"
    )
    @classmethod
    def validate_status(
        cls,
        value,
    ):
        value = (
            value
            .strip()
        )

        allowed = {
            "Assigned",
            "In Stitching",
            "Customer Notified",
            "Cancelled",
        }

        if value not in allowed:
            raise ValueError(
                "Status must be Assigned, "
                "In Stitching, "
                "Customer Notified or Cancelled."
            )

        return value


# ==========================================================
# RECEIVE FROM TAILOR
# ==========================================================

class TailoringReceiveCreate(BaseModel):

    quantity: int

    notes: Optional[
        str
    ] = None

    @field_validator(
        "quantity"
    )
    @classmethod
    def validate_quantity(
        cls,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Received quantity must be greater than zero."
            )

        return value


# ==========================================================
# DELIVER TO CUSTOMER
# ==========================================================

class TailoringDeliveryCreate(BaseModel):

    quantity: int

    notes: Optional[
        str
    ] = None

    @field_validator(
        "quantity"
    )
    @classmethod
    def validate_quantity(
        cls,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Delivery quantity must be greater than zero."
            )

        return value


# ==========================================================
# PENDING BILL ITEM
# ==========================================================

class PendingTailoringItemResponse(
    BaseModel
):

    bill_id: int
    bill_item_id: int

    invoice_number: str

    customer_id: int
    customer_name: str
    customer_phone: Optional[str]

    variant_id: int

    product_name: str
    sku: str
    size: Optional[str]
    color: Optional[str]

    ordered_qty: int
    delivered_qty: int
    pending_qty: int

    pending_k: int
    pending_r: int

    assigned_k: int
    assigned_r: int

    available_to_assign_k: int
    available_to_assign_r: int

    item_status: str


# ==========================================================
# JOB RESPONSE
# ==========================================================

class TailoringJobResponse(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    job_number: str

    shop_id: int

    bill_id: int
    bill_item_id: int
    sale_item_id: int

    customer_id: int
    supplier_id: int
    variant_id: int

    stock_type: str

    quantity: int
    received_quantity: int
    delivered_quantity: int

    status: str

    stitching_charge: Decimal

    expected_date: Optional[
        datetime
    ]

    assigned_at: datetime

    stitching_started_at: Optional[
        datetime
    ]

    received_at: Optional[
        datetime
    ]

    customer_notified_at: Optional[
        datetime
    ]

    delivered_at: Optional[
        datetime
    ]

    instructions: Optional[str]
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime


# ==========================================================
# DETAILED JOB RESPONSE
# ==========================================================

class TailoringJobDetailResponse(
    TailoringJobResponse
):

    invoice_number: str

    customer_name: str
    customer_phone: Optional[str]

    supplier_name: str

    product_name: str
    sku: str
    size: Optional[str]
    color: Optional[str]

    ready_quantity: int

    remaining_at_tailor: int

    remaining_to_customer: int

    tailor_paid_amount: Decimal
    tailor_due_amount: Decimal
    tailor_payment_status: str
