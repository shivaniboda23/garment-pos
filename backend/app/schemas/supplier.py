from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)


# ==========================================================
# HELPERS
# ==========================================================

def normalize_supplier_type(
    value: str,
):
    value = (
        str(value or "")
        .strip()
        .upper()
    )

    allowed = {
        "SUPPLIER",
        "TAILOR",
        "BOTH",
    }

    if value not in allowed:
        raise ValueError(
            "Supplier type must be "
            "SUPPLIER, TAILOR or BOTH."
        )

    return value


# ==========================================================
# CREATE SUPPLIER
# ==========================================================

class SupplierCreate(BaseModel):

    supplier_name: str

    supplier_type: str = (
        "SUPPLIER"
    )

    contact_person: Optional[
        str
    ] = None

    mobile: Optional[
        str
    ] = None

    email: Optional[
        str
    ] = None

    gst_number: Optional[
        str
    ] = None

    pan_number: Optional[
        str
    ] = None

    address: Optional[
        str
    ] = None

    city: Optional[
        str
    ] = None

    state: Optional[
        str
    ] = None

    pincode: Optional[
        str
    ] = None

    opening_balance: Decimal = Decimal(
        "0.00"
    )

    payment_terms: int = 30

    credit_limit: Decimal = Decimal(
        "0.00"
    )

    upi_id: Optional[
        str
    ] = None

    bank_name: Optional[
        str
    ] = None

    account_number: Optional[
        str
    ] = None

    ifsc_code: Optional[
        str
    ] = None

    notes: Optional[
        str
    ] = None

    # ======================================================
    # VALIDATORS
    # ======================================================

    @field_validator(
        "supplier_name"
    )
    @classmethod
    def validate_supplier_name(
        cls,
        value,
    ):
        value = value.strip()

        if not value:
            raise ValueError(
                "Supplier name is required."
            )

        return value

    @field_validator(
        "supplier_type"
    )
    @classmethod
    def validate_supplier_type(
        cls,
        value,
    ):
        return normalize_supplier_type(
            value
        )


# ==========================================================
# UPDATE SUPPLIER
# ==========================================================

class SupplierUpdate(BaseModel):

    supplier_name: Optional[
        str
    ] = None

    supplier_type: Optional[
        str
    ] = None

    contact_person: Optional[
        str
    ] = None

    mobile: Optional[
        str
    ] = None

    email: Optional[
        str
    ] = None

    gst_number: Optional[
        str
    ] = None

    pan_number: Optional[
        str
    ] = None

    address: Optional[
        str
    ] = None

    city: Optional[
        str
    ] = None

    state: Optional[
        str
    ] = None

    pincode: Optional[
        str
    ] = None

    payment_terms: Optional[
        int
    ] = None

    credit_limit: Optional[
        Decimal
    ] = None

    upi_id: Optional[
        str
    ] = None

    bank_name: Optional[
        str
    ] = None

    account_number: Optional[
        str
    ] = None

    ifsc_code: Optional[
        str
    ] = None

    notes: Optional[
        str
    ] = None

    is_active: Optional[
        bool
    ] = None

    # ======================================================
    # VALIDATORS
    # ======================================================

    @field_validator(
        "supplier_name"
    )
    @classmethod
    def validate_supplier_name(
        cls,
        value,
    ):
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError(
                "Supplier name cannot be empty."
            )

        return value

    @field_validator(
        "supplier_type"
    )
    @classmethod
    def validate_supplier_type(
        cls,
        value,
    ):
        if value is None:
            return value

        return normalize_supplier_type(
            value
        )


# ==========================================================
# RESPONSE
# ==========================================================

class SupplierResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    supplier_code: Optional[
        str
    ]

    supplier_name: str

    supplier_type: str

    contact_person: Optional[
        str
    ]

    mobile: Optional[
        str
    ]

    email: Optional[
        str
    ]

    gst_number: Optional[
        str
    ]

    pan_number: Optional[
        str
    ]

    address: Optional[
        str
    ]

    city: Optional[
        str
    ]

    state: Optional[
        str
    ]

    pincode: Optional[
        str
    ]

    opening_balance: Decimal

    payment_terms: int

    credit_limit: Decimal

    upi_id: Optional[
        str
    ]

    bank_name: Optional[
        str
    ]

    account_number: Optional[
        str
    ]

    ifsc_code: Optional[
        str
    ]

    notes: Optional[
        str
    ]

    is_active: bool