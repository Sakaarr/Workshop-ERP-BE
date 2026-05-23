import uuid
from datetime import datetime
from app.schemas.base import APIBase
from app.models.vehicle import FuelType


class VehicleCreate(APIBase):
    customer_id: uuid.UUID
    plate_number: str
    vin: str | None = None
    engine_number: str | None = None
    brand: str
    model: str
    year: int | None = None
    color: str | None = None
    fuel_type: FuelType = FuelType.PETROL
    last_odometer: int = 0


class VehicleUpdate(APIBase):
    plate_number: str | None = None
    vin: str | None = None
    engine_number: str | None = None
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    fuel_type: FuelType | None = None
    last_odometer: int | None = None


class VehicleResponse(APIBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    plate_number: str
    vin: str | None
    engine_number: str | None
    brand: str
    model: str
    year: int | None
    color: str | None
    fuel_type: FuelType
    last_odometer: int
    created_at: datetime
    updated_at: datetime


class VehicleWithCustomer(VehicleResponse):
    customer_name: str | None = None
    customer_phone: str | None = None