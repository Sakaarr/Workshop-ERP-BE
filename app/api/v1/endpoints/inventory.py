import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryListItem, StockAdjustment,
    SupplierCreate, SupplierUpdate, SupplierResponse,
)
from app.schemas.base import PaginatedResponse
from app.services.inventory_service import InventoryService
from app.api.v1.dependencies.auth import CurrentUser
from typing import List

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryListItem])
async def list_items(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    low_stock: bool = Query(default=False),
):
    return await InventoryService(session).list(page, page_size, search, category, low_stock)


@router.get("/categories", response_model=list[str])
async def get_categories(_: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).get_categories()


@router.get("/low-stock", response_model=List[InventoryListItem])
async def get_low_stock(_: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).get_low_stock()


@router.post("", response_model=InventoryItemResponse, status_code=201)
async def create_item(data: InventoryItemCreate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).create(data)


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_item(item_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await InventoryService(session).get(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_item(item_id: uuid.UUID, data: InventoryItemUpdate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await InventoryService(session).update(item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{item_id}/adjust-stock", response_model=InventoryItemResponse)
async def adjust_stock(item_id: uuid.UUID, data: StockAdjustment, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await InventoryService(session).adjust_stock(item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await InventoryService(session).delete(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Suppliers ─────────────────────────────────────────────
@router.get("/suppliers/all", response_model=PaginatedResponse[SupplierResponse])
async def list_suppliers(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20),
    search: str | None = Query(default=None),
):
    return await InventoryService(session).list_suppliers(page, page_size, search)


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(data: SupplierCreate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).create_supplier(data)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: uuid.UUID, data: SupplierUpdate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await InventoryService(session).update_supplier(supplier_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/suppliers/{supplier_id}", status_code=204)
async def delete_supplier(supplier_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await InventoryService(session).delete_supplier(supplier_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))