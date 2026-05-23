import uuid
from datetime import datetime
from decimal import Decimal
from app.schemas.base import APIBase
from app.models.invoice import PaymentStatus, PaymentMethod


class InvoiceCreate(APIBase):
    job_card_id: uuid.UUID
    customer_id: uuid.UUID
    discount_amount: Decimal = Decimal("0.00")
    discount_reason: str | None = None
    tax_rate: Decimal = Decimal("13.00")
    payment_method: PaymentMethod | None = None
    paid_amount: Decimal = Decimal("0.00")
    notes: str | None = None


class InvoiceUpdate(APIBase):
    discount_amount: Decimal | None = None
    discount_reason: str | None = None
    payment_method: PaymentMethod | None = None
    paid_amount: Decimal | None = None
    notes: str | None = None


class InvoiceResponse(APIBase):
    id: uuid.UUID
    invoice_number: str
    job_card_id: uuid.UUID
    customer_id: uuid.UUID
    subtotal: Decimal
    discount_amount: Decimal
    discount_reason: str | None
    taxable_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # enriched
    customer_name: str | None = None
    job_number: str | None = None
    vehicle_plate: str | None = None


class PaymentRecord(APIBase):
    amount: Decimal
    payment_method: PaymentMethod
    notes: str | None = None


class InvoiceListItem(APIBase):
    id: uuid.UUID
    invoice_number: str
    total_amount: Decimal
    paid_amount: Decimal
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None
    created_at: datetime
    customer_name: str | None = None
    job_number: str | None = None
    vehicle_plate: str | None = None