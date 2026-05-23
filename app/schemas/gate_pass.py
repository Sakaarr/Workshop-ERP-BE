import uuid
from datetime import datetime
from app.schemas.base import APIBase


class GatePassCreate(APIBase):
    invoice_id: uuid.UUID
    job_card_id: uuid.UUID
    notes: str | None = None


class GatePassResponse(APIBase):
    id: uuid.UUID
    invoice_id: uuid.UUID
    job_card_id: uuid.UUID
    verification_code: str
    is_used: bool
    notes: str | None
    created_at: datetime
    # enriched
    customer_name: str | None = None
    vehicle_plate: str | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    job_number: str | None = None
    invoice_number: str | None = None
    total_amount: str | None = None
    payment_status: str | None = None


class GatePassVerify(APIBase):
    verification_code: str