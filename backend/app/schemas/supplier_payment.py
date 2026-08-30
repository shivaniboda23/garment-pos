from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# CREATE SUPPLIER PAYMENT
# ==========================================================

class SupplierPaymentCreate(BaseModel):

    supplier_id: int

    purchase_id: int

    amount: Decimal = Field(
        gt=0,
    )

    payment_method: str

    reference_number: Optional[str] = None

    notes: Optional[str] = None

    payment_date: Optional[datetime] = None


# ==========================================================
# SUPPLIER PAYMENT RESPONSE
# ==========================================================

class SupplierPaymentResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    shop_id: int

    supplier_id: int

    purchase_id: int

    amount: Decimal

    payment_method: str

    reference_number: Optional[str]

    notes: Optional[str]

    payment_date: datetime

    created_at: datetime


# ==========================================================
# SUPPLIER BALANCE SUMMARY
# ==========================================================

class SupplierBalanceSummary(BaseModel):

    supplier_id: int

    supplier_name: str

    opening_balance: Decimal

    total_purchases: Decimal

    total_purchase_returns: Decimal

    total_payments: Decimal

    total_credit_applied: Decimal

    payable: Decimal

    supplier_credit: Decimal

    net_position: Decimal

    transaction_outstanding: Decimal


# ==========================================================
# SUPPLIER LEDGER ENTRY
# ==========================================================

class SupplierLedgerEntry(BaseModel):

    date: datetime

    transaction_type: str

    reference: str

    debit: Decimal

    credit: Decimal

    balance: Decimal


# ==========================================================
# SUPPLIER LEDGER RESPONSE
# ==========================================================

class SupplierLedgerResponse(BaseModel):

    supplier_id: int

    supplier_name: str

    opening_balance: Decimal

    entries: List[SupplierLedgerEntry]

    payable: Decimal

    supplier_credit: Decimal

    net_position: Decimal

    transaction_outstanding: Decimal


# ==========================================================
# APPLY SUPPLIER CREDIT
# ==========================================================

class SupplierCreditApplicationCreate(BaseModel):

    supplier_id: int

    purchase_id: int

    amount: Decimal = Field(
        gt=0,
    )

    reference_number: Optional[str] = None

    notes: Optional[str] = None

    applied_at: Optional[datetime] = None


# ==========================================================
# SUPPLIER CREDIT APPLICATION RESPONSE
# ==========================================================

class SupplierCreditApplicationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    shop_id: int

    supplier_id: int

    purchase_id: int

    amount: Decimal

    reference_number: Optional[str]

    notes: Optional[str]

    applied_at: datetime

    created_at: datetime