import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListItem
from app.schemas.base import PaginatedResponse


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CustomerRepository(session)

    async def list(self, page: int, page_size: int, search: str | None) -> PaginatedResponse[CustomerListItem]:
        skip = (page - 1) * page_size
        if search and search.strip():
            items, total = await self.repo.search(search.strip(), skip=skip, limit=page_size)
        else:
            items, total = await self.repo.list(skip=skip, limit=page_size)

        # get vehicle counts in bulk
        ids = [c.id for c in items]
        counts: dict[uuid.UUID, int] = {}
        if ids:
            q = select(Vehicle.customer_id, func.count(Vehicle.id)).where(
                Vehicle.customer_id.in_(ids), Vehicle.deleted_at.is_(None)
            ).group_by(Vehicle.customer_id)
            rows = (await self.session.execute(q)).all()
            counts = {row[0]: row[1] for row in rows}

        list_items = []
        for c in items:
            item = CustomerListItem.model_validate(c)
            item.vehicle_count = counts.get(c.id, 0)
            list_items.append(item)

        return PaginatedResponse(
            items=list_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, -(-total // page_size)),
        )

    async def get(self, id: uuid.UUID) -> CustomerResponse:
        c = await self.repo.get_or_raise(id)
        return CustomerResponse.model_validate(c)

    async def create(self, data: CustomerCreate) -> CustomerResponse:
        existing = await self.repo.get_by_phone(data.phone_primary)
        if existing:
            raise ValueError(f"A customer with phone {data.phone_primary} already exists")
        c = await self.repo.create(**data.model_dump())
        return CustomerResponse.model_validate(c)

    async def update(self, id: uuid.UUID, data: CustomerUpdate) -> CustomerResponse:
        c = await self.repo.get_or_raise(id)
        updated = await self.repo.update(c, **data.model_dump(exclude_none=True))
        return CustomerResponse.model_validate(updated)

    async def delete(self, id: uuid.UUID) -> None:
        c = await self.repo.get_or_raise(id)
        await self.repo.soft_delete(c)