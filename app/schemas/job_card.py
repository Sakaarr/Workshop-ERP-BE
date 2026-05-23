import uuid
from datetime import datetime
from decimal import Decimal
from app.schemas.base import APIBase
from app.models.job_card import JobStatus


class JobCardCreate(APIBase):
    vehicle_id: uuid.UUID
    customer_id: uuid.UUID
    complaint: str
    odometer_in: int = 0
    assigned_to: uuid.UUID | None = None
    estimated_cost: Decimal = Decimal("0.00")
    internal_notes: str | None = None


class JobCardUpdate(APIBase):
    status: JobStatus | None = None
    complaint: str | None = None
    diagnosis: str | None = None
    internal_notes: str | None = None
    assigned_to: uuid.UUID | None = None
    estimated_cost: Decimal | None = None
    labor_charge: Decimal | None = None
    odometer_out: int | None = None


class JobCardResponse(APIBase):
    id: uuid.UUID
    job_number: str
    vehicle_id: uuid.UUID
    customer_id: uuid.UUID
    assigned_to: uuid.UUID | None
    status: JobStatus
    complaint: str
    diagnosis: str | None
    internal_notes: str | None
    odometer_in: int
    odometer_out: int | None
    estimated_cost: Decimal
    labor_charge: Decimal
    created_at: datetime
    updated_at: datetime


class JobCardListItem(APIBase):
    id: uuid.UUID
    job_number: str
    status: JobStatus
    complaint: str
    estimated_cost: Decimal
    labor_charge: Decimal
    created_at: datetime
    # joined
    customer_name: str | None = None
    customer_phone: str | None = None
    vehicle_plate: str | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    assigned_to_name: str | None = None


class JobCardStatusUpdate(APIBase):
    status: JobStatus
    notes: str | None = None