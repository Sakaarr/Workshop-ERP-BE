import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job_card import JobCard, JobStatus
from app.repositories.base import BaseRepository


class JobCardRepository(BaseRepository[JobCard]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(JobCard, session)

    async def get_by_customer(self, customer_id: uuid.UUID) -> list[JobCard]:
        q = (
            select(JobCard)
            .where(JobCard.customer_id == customer_id, JobCard.deleted_at.is_(None))
            .order_by(JobCard.created_at.desc())
        )
        return list((await self.session.execute(q)).scalars().all())

    async def get_active(self) -> list[JobCard]:
        active = [JobStatus.WAITING, JobStatus.DIAGNOSING, JobStatus.REPAIRING, JobStatus.WAITING_PARTS, JobStatus.READY]
        q = (
            select(JobCard)
            .where(JobCard.status.in_(active), JobCard.deleted_at.is_(None))
            .order_by(JobCard.created_at.desc())
        )
        return list((await self.session.execute(q)).scalars().all())

    async def search(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list[JobCard], int]:
        condition = or_(JobCard.job_number.ilike(f"%{query}%"), JobCard.complaint.ilike(f"%{query}%"))
        return await self.list(skip=skip, limit=limit, filters=[condition])

    async def get_next_job_number(self) -> str:
        from datetime import datetime
        prefix = f"JC-{datetime.now().strftime('%y%m')}-"
        q = select(JobCard).where(JobCard.job_number.like(f"{prefix}%")).order_by(JobCard.job_number.desc())
        last = (await self.session.execute(q)).scalars().first()
        if last:
            try:
                seq = int(last.job_number.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"