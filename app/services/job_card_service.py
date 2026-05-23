import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.job_card import JobCard, JobStatus
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.user import User
from app.repositories.job_card import JobCardRepository
from app.schemas.job_card import JobCardCreate, JobCardUpdate, JobCardResponse, JobCardListItem, JobCardStatusUpdate
from app.schemas.base import PaginatedResponse


class JobCardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = JobCardRepository(session)

    async def list(self, page: int, page_size: int, search: str | None, status: JobStatus | None) -> PaginatedResponse[JobCardListItem]:
        skip = (page - 1) * page_size
        filters = []
        if status:
            filters.append(JobCard.status == status)
        if search and search.strip():
            items, total = await self.repo.search(search.strip(), skip=skip, limit=page_size)
        else:
            items, total = await self.repo.list(skip=skip, limit=page_size, filters=filters or None)

        enriched = []
        for j in items:
            item = JobCardListItem.model_validate(j)
            customer = await self.session.get(Customer, j.customer_id)
            vehicle = await self.session.get(Vehicle, j.vehicle_id)
            if customer:
                item.customer_name = customer.name
                item.customer_phone = customer.phone_primary
            if vehicle:
                item.vehicle_plate = vehicle.plate_number
                item.vehicle_brand = vehicle.brand
                item.vehicle_model = vehicle.model
            if j.assigned_to:
                staff = await self.session.get(User, j.assigned_to)
                if staff:
                    item.assigned_to_name = staff.full_name
            enriched.append(item)

        return PaginatedResponse(
            items=enriched, total=total, page=page, page_size=page_size,
            pages=max(1, -(-total // page_size)),
        )

    async def get(self, id: uuid.UUID) -> JobCardResponse:
        j = await self.repo.get_or_raise(id)
        return JobCardResponse.model_validate(j)

    async def create(self, data: JobCardCreate) -> JobCardResponse:
        job_number = await self.repo.get_next_job_number()
        j = await self.repo.create(
            job_number=job_number,
            **data.model_dump(),
        )
        return JobCardResponse.model_validate(j)

    async def update(self, id: uuid.UUID, data: JobCardUpdate) -> JobCardResponse:
        j = await self.repo.get_or_raise(id)
        updated = await self.repo.update(j, **data.model_dump(exclude_none=True))
        return JobCardResponse.model_validate(updated)

    async def update_status(self, id: uuid.UUID, data: JobCardStatusUpdate) -> JobCardResponse:
        j = await self.repo.get_or_raise(id)
        from datetime import datetime, timezone
        extra = {}
        if data.status == JobStatus.DELIVERED:
            extra["delivered_at"] = datetime.now(timezone.utc)
        updated = await self.repo.update(j, status=data.status, **extra)
        return JobCardResponse.model_validate(updated)

    async def delete(self, id: uuid.UUID) -> None:
        j = await self.repo.get_or_raise(id)
        await self.repo.soft_delete(j)