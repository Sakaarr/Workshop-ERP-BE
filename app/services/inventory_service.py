import uuid
from sqlalchemy.ext.asyncio import AsyncSession
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

    async def list(
        self,
        page: int,
        page_size: int,
        search: str | None,
        category: str | None,
        low_stock_only: bool = False,
    ) -> PaginatedResponse[InventoryListItem]:
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
                supplier = await self.session.get(
                    __import__("app.models.inventory", fromlist=["Supplier"]).Supplier,
                    item.supplier_id,
                )
                if supplier:
                    li.supplier_name = supplier.name
            enriched.append(li)

        return PaginatedResponse(
            items=enriched, total=total, page=page,
            page_size=page_size, pages=max(1, -(-total // page_size)),
        )

    async def get(self, item_id: uuid.UUID) -> InventoryItemResponse:
        item = await self.repo.get_or_raise(item_id)
        result = InventoryItemResponse.model_validate(item)
        result.is_low_stock = item.is_low_stock
        if item.supplier_id:
            from app.models.inventory import Supplier
            supplier = await self.session.get(Supplier, item.supplier_id)
            if supplier:
                result.supplier_name = supplier.name
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
        return [InventoryListItem.model_validate(i) for i in items]

    # ── Supplier methods ──────────────────────────────────
    async def list_suppliers(self, page: int, page_size: int, search: str | None) -> PaginatedResponse[SupplierResponse]:
        skip = (page - 1) * page_size
        if search and search.strip():
            items, total = await self.supplier_repo.search(search.strip(), skip=skip, limit=page_size)
        else:
            items, total = await self.supplier_repo.list(skip=skip, limit=page_size)
        return PaginatedResponse(
            items=[SupplierResponse.model_validate(s) for s in items],
            total=total, page=page, page_size=page_size,
            pages=max(1, -(-total // page_size)),
        )

    async def create_supplier(self, data: SupplierCreate) -> SupplierResponse:
        s = await self.supplier_repo.create(**data.model_dump())
        return SupplierResponse.model_validate(s)

    async def update_supplier(self, supplier_id: uuid.UUID, data: SupplierUpdate) -> SupplierResponse:
        s = await self.supplier_repo.get_or_raise(supplier_id)
        updated = await self.supplier_repo.update(s, **data.model_dump(exclude_none=True))
        return SupplierResponse.model_validate(updated)

    async def delete_supplier(self, supplier_id: uuid.UUID) -> None:
        s = await self.supplier_repo.get_or_raise(supplier_id)
        await self.supplier_repo.soft_delete(s)