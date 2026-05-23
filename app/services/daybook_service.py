import uuid
from decimal import Decimal
from datetime import date as DateType
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.invoice import DayBookRepository
from app.schemas.daybook import (
    DayBookEntryCreate, DayBookEntryUpdate,
    DayBookEntryResponse, DayBookSummary,
)
from app.schemas.base import PaginatedResponse


class DayBookService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DayBookRepository(session)

    async def create(self, data: DayBookEntryCreate, created_by: uuid.UUID) -> DayBookEntryResponse:
        entry = await self.repo.create(
            entry_type=data.entry_type,
            amount=data.amount,
            description=data.description,
            category=data.category,
            entry_date=data.entry_date,
            reference_id=data.reference_id,
            reference_type=data.reference_type,
            created_by=created_by,
        )
        return await self._enrich(entry)

    async def get_summary(self, date: str) -> DayBookSummary:
        entries = await self.repo.get_by_date(date)
        total_income = sum((e.amount for e in entries if e.entry_type == "income"), Decimal("0.00"))
        total_expense = sum((e.amount for e in entries if e.entry_type == "expense"), Decimal("0.00"))
        enriched = [await self._enrich(e) for e in entries]
        return DayBookSummary(
            date=date,
            total_income=total_income,
            total_expense=total_expense,
            net=total_income - total_expense,
            entries=enriched,
        )

    async def get_range_summary(self, start: str, end: str) -> list[DayBookSummary]:
        entries = await self.repo.get_by_date_range(start, end)
        by_date: dict[str, list] = {}
        for e in entries:
            by_date.setdefault(e.entry_date, []).append(e)

        summaries = []
        for d, day_entries in sorted(by_date.items()):
            income = sum((e.amount for e in day_entries if e.entry_type == "income"), Decimal("0.00"))
            expense = sum((e.amount for e in day_entries if e.entry_type == "expense"), Decimal("0.00"))
            enriched = [await self._enrich(e) for e in day_entries]
            summaries.append(DayBookSummary(
                date=d,
                total_income=income,
                total_expense=expense,
                net=income - expense,
                entries=enriched,
            ))
        return summaries

    async def list(self, page: int, page_size: int) -> PaginatedResponse[DayBookEntryResponse]:
        skip = (page - 1) * page_size
        items, total = await self.repo.list(skip=skip, limit=page_size)
        enriched = [await self._enrich(e) for e in items]
        return PaginatedResponse(
            items=enriched, total=total, page=page,
            page_size=page_size, pages=max(1, -(-total // page_size)),
        )

    async def delete(self, entry_id: uuid.UUID) -> None:
        e = await self.repo.get_or_raise(entry_id)
        await self.repo.soft_delete(e)

    async def _enrich(self, entry) -> DayBookEntryResponse:
        result = DayBookEntryResponse.model_validate(entry)
        user = await self.session.get(User, entry.created_by)
        if user:
            result.created_by_name = user.full_name
        return result