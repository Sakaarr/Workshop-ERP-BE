import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleWithCustomer
from app.schemas.base import PaginatedResponse
from app.services.vehicle_service import VehicleService
from app.api.v1.dependencies.auth import require_permission
from app.models.user import User

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

ViewVehicle   = Annotated[User, Depends(require_permission("vehicles.view"))]
CreateVehicle = Annotated[User, Depends(require_permission("vehicles.create"))]
EditVehicle   = Annotated[User, Depends(require_permission("vehicles.edit"))]
DeleteVehicle = Annotated[User, Depends(require_permission("vehicles.delete"))]


@router.get("", response_model=PaginatedResponse[VehicleResponse])
async def list_vehicles(
    _: ViewVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    customer_id: uuid.UUID | None = Query(default=None),
):
    return await VehicleService(session).list(page, page_size, search, customer_id)


@router.post("", response_model=VehicleResponse, status_code=201)
async def create_vehicle(
    data: VehicleCreate,
    _: CreateVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await VehicleService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{vehicle_id}", response_model=VehicleWithCustomer)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    _: ViewVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await VehicleService(session).get(vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    data: VehicleUpdate,
    _: EditVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await VehicleService(session).update(vehicle_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    _: DeleteVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await VehicleService(session).delete(vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/by-customer/{customer_id}", response_model=list[VehicleResponse])
async def vehicles_by_customer(
    customer_id: uuid.UUID,
    _: ViewVehicle,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await VehicleService(session).get_by_customer(customer_id)