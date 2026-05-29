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
from app.schemas.base import PaginatedResponse, BulkDeleteRequest
from app.services.inventory_service import InventoryService
from app.api.v1.dependencies.auth import require_permission
from app.models.user import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])

ViewInv    = Annotated[User, Depends(require_permission("inventory.view"))]
CreateInv  = Annotated[User, Depends(require_permission("inventory.create"))]
EditInv    = Annotated[User, Depends(require_permission("inventory.edit"))]
DeleteInv  = Annotated[User, Depends(require_permission("inventory.delete"))]
AdjustInv  = Annotated[User, Depends(require_permission("inventory.adjust_stock"))]


@router.get("", response_model=PaginatedResponse[InventoryListItem])
async def list_items(
    _: ViewInv,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    low_stock: bool = Query(default=False),
):
    return await InventoryService(session).list(page, page_size, search, category, low_stock)


@router.get("/categories", response_model=list[str])
async def get_categories(_: ViewInv, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).get_categories()


@router.get("/low-stock", response_model=list[InventoryListItem])
async def get_low_stock(_: ViewInv, session: Annotated[AsyncSession, Depends(get_db)]):
    return await InventoryService(session).get_low_stock()


@router.post("", response_model=InventoryItemResponse, status_code=201)
async def create_item(
    data: InventoryItemCreate,
    _: CreateInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await InventoryService(session).create(data)


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_item(
    item_id: uuid.UUID,
    _: ViewInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InventoryService(session).get(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: uuid.UUID,
    data: InventoryItemUpdate,
    _: EditInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InventoryService(session).update(item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{item_id}/adjust-stock", response_model=InventoryItemResponse)
async def adjust_stock(
    item_id: uuid.UUID,
    data: StockAdjustment,
    _: AdjustInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InventoryService(session).adjust_stock(item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: uuid.UUID,
    _: DeleteInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await InventoryService(session).delete(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk-delete", status_code=204)
async def bulk_delete_items(
    data: BulkDeleteRequest,
    _: DeleteInv,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await InventoryService(session).bulk_delete_items(data.ids)
