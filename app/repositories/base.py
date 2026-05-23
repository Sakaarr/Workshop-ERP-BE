import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Generic async repository with common CRUD operations."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> ModelT | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: uuid.UUID) -> ModelT:
        obj = await self.get(id)
        if obj is None:
            raise ValueError(f"{self.model.__name__} with id={id} not found")
        return obj

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        filters: list[Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        base_filter = [self.model.deleted_at.is_(None)]
        if filters:
            base_filter.extend(filters)

        count_q = select(func.count()).select_from(self.model).where(and_(*base_filter))
        total = (await self.session.execute(count_q)).scalar_one()

        items_q = (
            select(self.model)
            .where(and_(*base_filter))
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        items = list((await self.session.execute(items_q)).scalars().all())
        return items, total

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            if value is not None:
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> None:
        obj.soft_delete()
        await self.session.flush()

    async def hard_delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()