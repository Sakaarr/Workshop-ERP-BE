import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import InventoryItem, Supplier
from app.repositories.base import BaseRepository
from typing import List, Tuple

class InventoryRepository(BaseRepository[InventoryItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InventoryItem, session)

    async def search(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list[InventoryItem], int]:
        condition = or_(
            InventoryItem.name.ilike(f"%{query}%"),
            InventoryItem.part_number.ilike(f"%{query}%"),
            InventoryItem.category.ilike(f"%{query}%"),
            InventoryItem.barcode.ilike(f"%{query}%"),
        )
        return await self.list(skip=skip, limit=limit, filters=[condition])

    async def get_low_stock(self) -> list[InventoryItem]:
        from sqlalchemy import text
        q = (
            select(InventoryItem)
            .where(
                InventoryItem.deleted_at.is_(None),
                InventoryItem.quantity <= InventoryItem.low_stock_threshold,
            )
            .order_by(InventoryItem.quantity.asc())
        )
        return list((await self.session.execute(q)).scalars().all())

    async def get_by_category(self, category: str) -> list[InventoryItem]:
        q = select(InventoryItem).where(
            InventoryItem.category == category,
            InventoryItem.deleted_at.is_(None),
        )
        return list((await self.session.execute(q)).scalars().all())

    async def get_categories(self) -> List[str]:
        from sqlalchemy import distinct
        q = select(distinct(InventoryItem.category)).where(
            InventoryItem.deleted_at.is_(None)
        )
        result = await self.session.execute(q)
        return [row[0] for row in result.all()]

    async def adjust_stock(self, item_id: uuid.UUID, delta: int) -> InventoryItem:
        item = await self.get_or_raise(item_id)
        new_qty = item.quantity + delta
        if new_qty < 0:
            raise ValueError(f"Insufficient stock. Current: {item.quantity}, Requested: {abs(delta)}")
        item.quantity = new_qty
        await self.session.flush()
        await self.session.refresh(item)
        return item


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Supplier, session)

    async def search(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list[Supplier], int]:
        condition = or_(
            Supplier.name.ilike(f"%{query}%"),
            Supplier.phone.ilike(f"%{query}%"),
        )
        return await self.list(skip=skip, limit=limit, filters=[condition])