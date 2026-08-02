from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# -------------------------
# Create Supplier
# -------------------------

class SupplierCreate(BaseModel):
    supplier_name: str
    contact_person: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    gst_number: Optional[str] = None
    pan_number: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    opening_balance: Decimal = Decimal("0.00")

    payment_terms: int = 30
    credit_limit: Decimal = Decimal("0.00")

    upi_id: Optional[str] = None

    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

    notes: Optional[str] = None


# -------------------------
# Update Supplier
# -------------------------

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    contact_person: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None

    gst_number: Optional[str] = None
    pan_number: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    payment_terms: Optional[int] = None
    credit_limit: Optional[Decimal] = None

    upi_id: Optional[str] = None

    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

    notes: Optional[str] = None

    is_active: Optional[bool] = None


# -------------------------
# Response
# -------------------------

class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_code: Optional[str]

    supplier_name: str
    contact_person: Optional[str]

    mobile: Optional[str]
    email: Optional[str]

    gst_number: Optional[str]
    pan_number: Optional[str]

    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]

    opening_balance: Decimal

    payment_terms: int
    credit_limit: Decimal

    upi_id: Optional[str]

    bank_name: Optional[str]
    account_number: Optional[str]
    ifsc_code: Optional[str]

    notes: Optional[str]

    is_active: bool