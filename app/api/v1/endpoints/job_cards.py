import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.job_card import JobStatus
from app.schemas.job_card import JobCardCreate, JobCardUpdate, JobCardResponse, JobCardListItem, JobCardStatusUpdate
from app.schemas.base import PaginatedResponse
from app.services.job_card_service import JobCardService
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/job-cards", tags=["Job Cards"])


@router.get("", response_model=PaginatedResponse[JobCardListItem])
async def list_jobs(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: JobStatus | None = Query(default=None),
):
    return await JobCardService(session).list(page, page_size, search, status)


@router.post("", response_model=JobCardResponse, status_code=201)
async def create_job(data: JobCardCreate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await JobCardService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}", response_model=JobCardResponse)
async def get_job(job_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await JobCardService(session).get(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{job_id}", response_model=JobCardResponse)
async def update_job(job_id: uuid.UUID, data: JobCardUpdate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await JobCardService(session).update(job_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{job_id}/status", response_model=JobCardResponse)
async def update_status(job_id: uuid.UUID, data: JobCardStatusUpdate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await JobCardService(session).update_status(job_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await JobCardService(session).delete(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))