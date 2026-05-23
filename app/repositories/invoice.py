import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import Invoice, DayBookEntry
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Invoice, session)

    async def get_by_job_card(self, job_card_id: uuid.UUID) -> Invoice | None:
        q = select(Invoice).where(
            Invoice.job_card_id == job_card_id,
            Invoice.deleted_at.is_(None),
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_next_invoice_number(self) -> str:
        from datetime import datetime
        prefix = f"INV-{datetime.now().strftime('%y%m')}-"
        q = (
            select(Invoice)
            .where(Invoice.invoice_number.like(f"{prefix}%"))
            .order_by(Invoice.invoice_number.desc())
        )
        last = (await self.session.execute(q)).scalars().first()
        seq = 1
        if last:
            try:
                seq = int(last.invoice_number.split("-")[-1]) + 1
            except Exception:
                seq = 1
        return f"{prefix}{seq:04d}"


class DayBookRepository(BaseRepository[DayBookEntry]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DayBookEntry, session)

    async def get_by_date(self, date: str) -> list[DayBookEntry]:
        q = (
            select(DayBookEntry)
            .where(
                DayBookEntry.entry_date == date,
                DayBookEntry.deleted_at.is_(None),
            )
            .order_by(DayBookEntry.created_at.asc())
        )
        return list((await self.session.execute(q)).scalars().all())

    async def get_by_date_range(self, start: str, end: str) -> list[DayBookEntry]:
        q = (
            select(DayBookEntry)
            .where(
                DayBookEntry.entry_date >= start,
                DayBookEntry.entry_date <= end,
                DayBookEntry.deleted_at.is_(None),
            )
            .order_by(DayBookEntry.entry_date.asc(), DayBookEntry.created_at.asc())
        )
        return list((await self.session.execute(q)).scalars().all())