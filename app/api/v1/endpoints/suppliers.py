import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.inventory import SupplierCreate, SupplierUpdate, SupplierResponse
from app.schemas.base import PaginatedResponse
from app.services.inventory_service import InventoryService
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=PaginatedResponse[SupplierResponse])
async def list_suppliers(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20),
    search: str | None = Query(default=None),
):
    return await InventoryService(session).list_suppliers(page, page_size, search)


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await InventoryService(session).create_supplier(data)


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        svc = InventoryService(session)
        items, _ = await svc.supplier_repo.list(filters=None)
        s = await svc.supplier_repo.get_or_raise(supplier_id)
        return SupplierResponse.model_validate(s)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    data: SupplierUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InventoryService(session).update_supplier(supplier_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await InventoryService(session).delete_supplier(supplier_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))