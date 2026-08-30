from decimal import Decimal
from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# ==========================================================
# BILL ITEM CREATE
# ==========================================================

class BillItemCreate(BaseModel):

    variant_id: int

    # ------------------------------------------------------
    # Total quantity customer is paying/ordering.
    # ------------------------------------------------------

    ordered_qty: int

    # ------------------------------------------------------
    # QUANTITY DELIVERED NOW FROM CURRENT STOCK
    # ------------------------------------------------------

    k_quantity: int = 0
    r_quantity: int = 0

    # ------------------------------------------------------
    # QUANTITY STILL PENDING
    #
    # This tells us whether pending items are K or R.
    # This will later connect directly to tailoring.
    # ------------------------------------------------------

    pending_k_quantity: int = 0
    pending_r_quantity: int = 0

    selling_price: Decimal

    discount: Decimal = Decimal(
        "0"
    )

    gst_percentage: Decimal = Decimal(
        "0"
    )

    # ======================================================
    # VALIDATORS
    # ======================================================

    @field_validator(
        "ordered_qty"
    )
    @classmethod
    def validate_ordered_qty(
        cls,
        value,
    ):
        if value <= 0:
            raise ValueError(
                "Ordered quantity must be "
                "greater than zero."
            )

        return value

    @field_validator(
        "k_quantity",
        "r_quantity",
        "pending_k_quantity",
        "pending_r_quantity",
    )
    @classmethod
    def validate_quantities(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Item quantities cannot "
                "be negative."
            )

        return value

    @field_validator(
        "selling_price",
        "discount",
        "gst_percentage",
    )
    @classmethod
    def validate_money_fields(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Money values cannot "
                "be negative."
            )

        return value

    # ======================================================
    # QUANTITY SPLIT
    #
    # ordered quantity must equal:
    #
    # delivered K
    # + delivered R
    # + pending K
    # + pending R
    # ======================================================

    @model_validator(
        mode="after"
    )
    def validate_split_quantities(
        self,
    ):
        total_split = (
            self.k_quantity
            + self.r_quantity
            + self.pending_k_quantity
            + self.pending_r_quantity
        )

        if (
            self.ordered_qty
            != total_split
        ):
            raise ValueError(
                "Ordered quantity must equal "
                "delivered K + delivered R + "
                "pending K + pending R."
            )

        return self


# ==========================================================
# PAYMENT
# ==========================================================

class PaymentCreate(BaseModel):

    payment_mode: str

    amount: Decimal

    @field_validator(
        "payment_mode"
    )
    @classmethod
    def validate_payment_mode(
        cls,
        value,
    ):
        value = value.strip()

        if not value:
            raise ValueError(
                "Payment mode is required."
            )

        return value

    @field_validator(
        "amount"
    )
    @classmethod
    def validate_amount(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Payment amount cannot "
                "be negative."
            )

        return value


# ==========================================================
# CREATE BILL
# ==========================================================

class BillCreate(BaseModel):

    customer_id: Optional[
        int
    ] = None

    subtotal: Optional[
        Decimal
    ] = None

    discount: Decimal = Decimal(
        "0"
    )

    gst: Optional[
        Decimal
    ] = None

    grand_total: Optional[
        Decimal
    ] = None

    items: List[
        BillItemCreate
    ]

    payments: List[
        PaymentCreate
    ] = Field(
        default_factory=list
    )

    remarks: Optional[
        str
    ] = None

    @field_validator(
        "discount"
    )
    @classmethod
    def validate_discount(
        cls,
        value,
    ):
        if value < 0:
            raise ValueError(
                "Discount cannot be negative."
            )

        return value

    @model_validator(
        mode="after"
    )
    def validate_items(
        self,
    ):
        if not self.items:
            raise ValueError(
                "At least one bill item "
                "is required."
            )

        return self


# ==========================================================
# BILL ITEM RESPONSE
# ==========================================================

class BillItemResponse(BaseModel):

    id: int

    variant_id: Optional[
        int
    ] = None

    product_id: Optional[
        int
    ] = None

    ordered_qty: int

    delivered_qty: int

    pending_qty: int

    # ------------------------------------------------------
    # Total K/R ordered.
    #
    # Pending K =
    #     k_quantity - k_delivered_qty
    #
    # Pending R =
    #     r_quantity - r_delivered_qty
    # ------------------------------------------------------

    k_quantity: int
    r_quantity: int

    k_delivered_qty: int
    r_delivered_qty: int

    selling_price: Decimal

    discount: Decimal

    gst_percentage: Decimal

    gst: Decimal

    total: Decimal

    item_status: str

    class Config:
        from_attributes = True


# ==========================================================
# PAYMENT RESPONSE
# ==========================================================

class PaymentResponse(BaseModel):

    id: int

    payment_method: str

    amount: Decimal

    class Config:
        from_attributes = True


# ==========================================================
# BILL RESPONSE
# ==========================================================

class BillResponse(BaseModel):

    id: int

    sale_id: Optional[
        int
    ]

    invoice_number: str

    customer_id: Optional[
        int
    ]

    subtotal: Decimal

    discount: Decimal

    gst: Decimal

    grand_total: Decimal

    payment_method: Optional[
        str
    ]

    payment_status: str

    bill_status: str

    remarks: Optional[
        str
    ]

    items: List[
        BillItemResponse
    ]

    payments: List[
        PaymentResponse
    ]

    class Config:
        from_attributes = True