import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.repositories.vehicle import VehicleRepository
from app.repositories.customer import CustomerRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleWithCustomer
from app.schemas.base import PaginatedResponse
from typing import List


class VehicleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VehicleRepository(session)
        self.customer_repo = CustomerRepository(session)

    async def list(self, page: int, page_size: int, search: str | None, customer_id: uuid.UUID | None) -> PaginatedResponse[VehicleResponse]:
        skip = (page - 1) * page_size
        if customer_id:
            items = await self.repo.get_by_customer(customer_id)
            total = len(items)
            items = items[skip: skip + page_size]
        elif search and search.strip():
            items, total = await self.repo.search(search.strip(), skip=skip, limit=page_size)
        else:
            items, total = await self.repo.list(skip=skip, limit=page_size)
        return PaginatedResponse(
            items=[VehicleResponse.model_validate(v) for v in items],
            total=total, page=page, page_size=page_size,
            pages=max(1, -(-total // page_size)),
        )

    async def get(self, id: uuid.UUID) -> VehicleWithCustomer:
        v = await self.repo.get_or_raise(id)
        customer = await self.customer_repo.get(v.customer_id)
        result = VehicleWithCustomer.model_validate(v)
        if customer:
            result.customer_name = customer.name
            result.customer_phone = customer.phone_primary
        return result

    async def get_by_customer(self, customer_id: uuid.UUID) -> List[VehicleResponse]:
        items = await self.repo.get_by_customer(customer_id)
        return [VehicleResponse.model_validate(v) for v in items]

    async def create(self, data: VehicleCreate) -> VehicleResponse:
        await self.customer_repo.get_or_raise(data.customer_id)
        existing = await self.repo.get_by_plate(data.plate_number)
        if existing:
            raise ValueError(f"Vehicle with plate {data.plate_number} already exists")
        v = await self.repo.create(**data.model_dump())
        return VehicleResponse.model_validate(v)

    async def update(self, id: uuid.UUID, data: VehicleUpdate) -> VehicleResponse:
        v = await self.repo.get_or_raise(id)
        updated = await self.repo.update(v, **data.model_dump(exclude_none=True))
        return VehicleResponse.model_validate(updated)

    async def delete(self, id: uuid.UUID) -> None:
        v = await self.repo.get_or_raise(id)
        await self.repo.soft_delete(v)

    async def bulk_delete(self, ids: List[uuid.UUID]) -> None:
        for vehicle_id in ids:
            vehicle = await self.repo.get_or_raise(vehicle_id)
            await self.repo.soft_delete(vehicle)
