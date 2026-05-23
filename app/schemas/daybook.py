import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from app.schemas.base import APIBase


class DayBookEntryCreate(APIBase):
    entry_type: Literal["income", "expense"]
    amount: Decimal
    description: str
    category: str
    entry_date: str          # YYYY-MM-DD
    reference_id: uuid.UUID | None = None
    reference_type: str | None = None


class DayBookEntryUpdate(APIBase):
    amount: Decimal | None = None
    description: str | None = None
    category: str | None = None


class DayBookEntryResponse(APIBase):
    id: uuid.UUID
    entry_type: str
    amount: Decimal
    description: str
    category: str
    entry_date: str
    reference_id: uuid.UUID | None
    reference_type: str | None
    created_by: uuid.UUID
    created_at: datetime
    created_by_name: str | None = None


class DayBookSummary(APIBase):
    date: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    entries: list[DayBookEntryResponse]