from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TailorPaymentCreate(BaseModel):
    tailoring_job_id: int
    amount: Decimal = Field(gt=0)
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    payment_date: Optional[datetime] = None


class TailorPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: int
    supplier_id: int
    tailoring_job_id: int
    amount: Decimal
    payment_method: str
    reference_number: Optional[str]
    notes: Optional[str]
    payment_date: datetime
    created_at: datetime


class TailoringJobPaymentSummary(BaseModel):
    tailoring_job_id: int
    job_number: str
    supplier_id: int
    supplier_name: str
    invoice_number: str
    product_name: str
    quantity: int
    stitching_charge: Decimal
    paid_amount: Decimal
    due_amount: Decimal
    payment_status: str
    payments: List[TailorPaymentResponse]


class TailorDueItem(BaseModel):
    tailoring_job_id: int
    job_number: str
    supplier_id: int
    supplier_name: str
    invoice_number: str
    product_name: str
    customer_name: str
    stitching_charge: Decimal
    paid_amount: Decimal
    due_amount: Decimal
    job_status: str
    assigned_at: datetime


class TailorBalanceSummary(BaseModel):
    supplier_id: int
    supplier_name: str
    total_jobs: int
    total_agreed_charges: Decimal
    total_paid: Decimal
    payable: Decimal


class TailorLedgerEntry(BaseModel):
    date: datetime
    transaction_type: str
    reference: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


class TailorLedgerResponse(BaseModel):
    supplier_id: int
    supplier_name: str
    entries: List[TailorLedgerEntry]
    total_agreed_charges: Decimal
    total_paid: Decimal
    payable: Decimal
