import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.schemas.daybook import DayBookEntryCreate, DayBookEntryResponse, DayBookSummary
from app.schemas.base import PaginatedResponse
from app.services.daybook_service import DayBookService
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/daybook", tags=["Day Book"])


@router.get("/summary", response_model=DayBookSummary)
async def get_daily_summary(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    date: str = Query(default=str(date.today())),
):
    return await DayBookService(session).get_summary(date)


@router.get("/range", response_model=list[DayBookSummary])
async def get_range_summary(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    start: str = Query(...),
    end: str = Query(...),
):
    return await DayBookService(session).get_range_summary(start, end)


@router.get("", response_model=PaginatedResponse[DayBookEntryResponse])
async def list_entries(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    return await DayBookService(session).list(page, page_size)


@router.post("", response_model=DayBookEntryResponse, status_code=201)
async def create_entry(
    data: DayBookEntryCreate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DayBookService(session).create(data, current_user.id)


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await DayBookService(session).delete(entry_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))