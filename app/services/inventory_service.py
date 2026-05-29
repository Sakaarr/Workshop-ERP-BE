import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import InventoryItem, Supplier
from app.repositories.inventory import InventoryRepository, SupplierRepository
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryListItem, StockAdjustment,
    SupplierCreate, SupplierUpdate, SupplierResponse,
)
from app.schemas.base import PaginatedResponse
from typing import List


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InventoryRepository(session)
        self.supplier_repo = SupplierRepository(session)

    async def list(self, page, page_size, search, category, low_stock_only=False) -> PaginatedResponse[InventoryListItem]:
        skip = (page - 1) * page_size
        if low_stock_only:
            items = await self.repo.get_low_stock()
            total = len(items)
            items = items[skip: skip + page_size]
        elif search and search.strip():
            items, total = await self.repo.search(search.strip(), skip=skip, limit=page_size)
        elif category:
            items = await self.repo.get_by_category(category)
            total = len(items)
            items = items[skip: skip + page_size]
        else:
            items, total = await self.repo.list(skip=skip, limit=page_size)

        enriched = []
        for item in items:
            li = InventoryListItem.model_validate(item)
            li.is_low_stock = item.is_low_stock
            if item.supplier_id:
                supplier = await self.session.get(Supplier, item.supplier_id)
                if supplier:
                    li.supplier_name = supplier.name
            enriched.append(li)
        return PaginatedResponse(items=enriched, total=total, page=page, page_size=page_size, pages=max(1, -(-total // page_size)))

    async def get(self, item_id: uuid.UUID) -> InventoryItemResponse:
        item = await self.repo.get_or_raise(item_id)
        result = InventoryItemResponse.model_validate(item)
        result.is_low_stock = item.is_low_stock
        if item.supplier_id:
            supplier = await self.session.get(Supplier, item.supplier_id)
            if supplier:
                result.supplier_name = supplier.name
                result.supplier_phone = supplier.phone
        return result

    async def create(self, data: InventoryItemCreate) -> InventoryItemResponse:
        item = await self.repo.create(**data.model_dump())
        return await self.get(item.id)

    async def update(self, item_id: uuid.UUID, data: InventoryItemUpdate) -> InventoryItemResponse:
        item = await self.repo.get_or_raise(item_id)
        await self.repo.update(item, **data.model_dump(exclude_none=True))
        return await self.get(item_id)

    async def adjust_stock(self, item_id: uuid.UUID, data: StockAdjustment) -> InventoryItemResponse:
        await self.repo.adjust_stock(item_id, data.quantity_change)
        return await self.get(item_id)

    async def delete(self, item_id: uuid.UUID) -> None:
        item = await self.repo.get_or_raise(item_id)
        await self.repo.soft_delete(item)

    async def get_categories(self) -> List[str]:
        return await self.repo.get_categories()

    async def get_low_stock(self) -> List[InventoryListItem]:
        items = await self.repo.get_low_stock()
        enriched = []
        for item in items:
            li = InventoryListItem.model_validate(item)
            li.is_low_stock = item.is_low_stock
            if item.supplier_id:
                supplier = await self.session.get(Supplier, item.supplier_id)
                if supplier:
                    li.supplier_name = supplier.name
            enriched.append(li)
        return enriched

    async def list_suppliers(self, page, page_size, search) -> PaginatedResponse[SupplierResponse]:
        skip = (page - 1) * page_size
        if search and search.strip():
            items, total = await self.supplier_repo.search(search.strip(), skip=skip, limit=page_size)
        else:
            items, total = await self.supplier_repo.list(skip=skip, limit=page_size)

        enriched = []
        for s in items:
            resp = SupplierResponse.model_validate(s)
            q = select(func.count()).select_from(InventoryItem).where(
                InventoryItem.supplier_id == s.id,
                InventoryItem.deleted_at.is_(None),
            )
            resp.parts_count = (await self.session.execute(q)).scalar_one()
            enriched.append(resp)
        return PaginatedResponse(items=enriched, total=total, page=page, page_size=page_size, pages=max(1, -(-total // page_size)))

    async def create_supplier(self, data: SupplierCreate) -> SupplierResponse:
        s = await self.supplier_repo.create(**data.model_dump())
        result = SupplierResponse.model_validate(s)
        result.parts_count = 0
        return result

    async def update_supplier(self, supplier_id: uuid.UUID, data: SupplierUpdate) -> SupplierResponse:
        s = await self.supplier_repo.get_or_raise(supplier_id)
        updated = await self.supplier_repo.update(s, **data.model_dump(exclude_none=True))
        result = SupplierResponse.model_validate(updated)
        q = select(func.count()).select_from(InventoryItem).where(
            InventoryItem.supplier_id == supplier_id,
            InventoryItem.deleted_at.is_(None),
        )
        result.parts_count = (await self.session.execute(q)).scalar_one()
        return result

    async def delete_supplier(self, supplier_id: uuid.UUID) -> None:
        s = await self.supplier_repo.get_or_raise(supplier_id)
        await self.supplier_repo.soft_delete(s)

    async def bulk_delete_items(self, ids: List[uuid.UUID]) -> None:
        for item_id in ids:
            item = await self.repo.get_or_raise(item_id)
            await self.repo.soft_delete(item)

    async def bulk_delete_suppliers(self, ids: List[uuid.UUID]) -> None:
        for supplier_id in ids:
            supplier = await self.supplier_repo.get_or_raise(supplier_id)
            await self.supplier_repo.soft_delete(supplier)
