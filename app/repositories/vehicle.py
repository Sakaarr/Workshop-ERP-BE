import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Vehicle, session)

    async def get_by_customer(self, customer_id: uuid.UUID) -> list[Vehicle]:
        q = select(Vehicle).where(
            Vehicle.customer_id == customer_id,
            Vehicle.deleted_at.is_(None),
        ).order_by(Vehicle.created_at.desc())
        return list((await self.session.execute(q)).scalars().all())

    async def search(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list[Vehicle], int]:
        condition = or_(
            Vehicle.plate_number.ilike(f"%{query}%"),
            Vehicle.brand.ilike(f"%{query}%"),
            Vehicle.model.ilike(f"%{query}%"),
            Vehicle.vin.ilike(f"%{query}%"),
        )
        return await self.list(skip=skip, limit=limit, filters=[condition])

    async def get_by_plate(self, plate: str) -> Vehicle | None:
        q = select(Vehicle).where(
            Vehicle.plate_number == plate,
            Vehicle.deleted_at.is_(None),
        )
        return (await self.session.execute(q)).scalar_one_or_none()