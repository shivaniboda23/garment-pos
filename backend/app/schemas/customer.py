from typing import Optional

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    shop_id: int

    customer_name: str

    phone: str

    email: Optional[EmailStr] = None

    address: Optional[str] = None

    gst_number: Optional[str] = None


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None

    phone: Optional[str] = None

    email: Optional[EmailStr] = None

    address: Optional[str] = None

    gst_number: Optional[str] = None

    is_active: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: int

    shop_id: int

    customer_name: str

    phone: str

    email: Optional[str]

    address: Optional[str]

    gst_number: Optional[str]

    is_active: bool

    class Config:
        from_attributes = True