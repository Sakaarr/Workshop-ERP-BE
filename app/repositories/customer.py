from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Customer, session)

    async def search(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list[Customer], int]:
        condition = or_(
            Customer.name.ilike(f"%{query}%"),
            Customer.phone_primary.ilike(f"%{query}%"),
            Customer.phone_secondary.ilike(f"%{query}%"),
            Customer.pan_vat.ilike(f"%{query}%"),
            Customer.city.ilike(f"%{query}%"),
        )
        filters = [Customer.deleted_at.is_(None), condition]
        return await self.list(skip=skip, limit=limit, filters=[condition])

    async def get_by_phone(self, phone: str) -> Customer | None:
        q = select(Customer).where(
            Customer.phone_primary == phone,
            Customer.deleted_at.is_(None),
        )
        return (await self.session.execute(q)).scalar_one_or_none()