from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.base import PaginatedResponse
from app.services.activity_log_service import ActivityLogService, ActivityLogResponse
from app.api.v1.dependencies.auth import AdminUser
from datetime import date

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=PaginatedResponse[ActivityLogResponse])
async def list_logs(
    _: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),  # ← date, not str
    date_to: date | None = Query(default=None),    # ← date, not str
    search: str | None = Query(default=None),
):
    return await ActivityLogService(session).list(
        page=page, page_size=page_size,
        action_filter=action, user_id_filter=user_id,
        resource_type_filter=resource_type,
        date_from=date_from, date_to=date_to, search=search,
    )


@router.get("/recent", response_model=list[ActivityLogResponse])
async def recent_logs(
    _: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
):
    return await ActivityLogService(session).get_recent(limit)