import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import EmailStr
from app.schemas.base import APIBase


class CustomerCreate(APIBase):
    name: str
    phone_primary: str
    phone_secondary: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    pan_vat: str | None = None
    notes: str | None = None


class CustomerUpdate(APIBase):
    name: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    pan_vat: str | None = None
    notes: str | None = None


class CustomerResponse(APIBase):
    id: uuid.UUID
    name: str
    phone_primary: str
    phone_secondary: str | None
    email: str | None
    address: str | None
    city: str | None
    pan_vat: str | None
    notes: str | None
    outstanding_balance: Decimal
    created_at: datetime
    updated_at: datetime


class CustomerListItem(APIBase):
    id: uuid.UUID
    name: str
    phone_primary: str
    phone_secondary: str | None
    city: str | None
    outstanding_balance: Decimal
    vehicle_count: int = 0
    created_at: datetime