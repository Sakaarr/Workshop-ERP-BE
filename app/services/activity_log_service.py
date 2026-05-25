import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.base import PaginatedResponse, APIBase
from pydantic import ConfigDict
from typing import List
from datetime import datetime, timezone, date


class ActivityLogResponse(APIBase):
    id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str | None
    user_email: str | None
    user_role: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    resource_label: str | None
    description: str
    extra_metadata: dict | None
    ip_address: str | None
    created_at: datetime


class ActivityLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        action: str,
        description: str,
        user: User | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_label: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        entry = ActivityLog(
            user_id=user.id if user else None,
            user_name=user.full_name if user else None,
            user_email=user.email if user else None,
            user_role=user.role if user else None,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_label=resource_label,
            extra_metadata=extra_metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(entry)
        await self.session.flush()

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        action_filter: str | None = None,
        user_id_filter: str | None = None,
        resource_type_filter: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ActivityLogResponse]:
        skip = (page - 1) * page_size
        filters = [ActivityLog.deleted_at.is_(None)]

        if action_filter:
            filters.append(ActivityLog.action.ilike(f"%{action_filter}%"))
        if user_id_filter:
            try:
                uid = uuid.UUID(user_id_filter)
                filters.append(ActivityLog.user_id == uid)
            except ValueError:
                pass
        if resource_type_filter:
            filters.append(ActivityLog.resource_type == resource_type_filter)
        from sqlalchemy import cast, Date

        if date_from:
            filters.append(cast(ActivityLog.created_at, Date) >= date_from)
        if date_to:
            filters.append(cast(ActivityLog.created_at, Date) <= date_to)
            filters.append(func.date(ActivityLog.created_at) <= date_to)
        if search:
            filters.append(or_(
                ActivityLog.description.ilike(f"%{search}%"),
                ActivityLog.user_name.ilike(f"%{search}%"),
                ActivityLog.user_email.ilike(f"%{search}%"),
                ActivityLog.resource_label.ilike(f"%{search}%"),
            ))

        count_q = select(func.count()).select_from(ActivityLog).where(and_(*filters))
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(ActivityLog)
            .where(and_(*filters))
            .order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(page_size)
        )
        items = list((await self.session.execute(q)).scalars().all())
        return PaginatedResponse(
            items=[ActivityLogResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            pages=max(1, -(-total // page_size)),
        )

    async def get_action_types(self) -> List[str]:
        from sqlalchemy import distinct
        q = select(distinct(ActivityLog.action)).where(
            ActivityLog.deleted_at.is_(None)
        ).order_by(ActivityLog.action)
        return [(await self.session.execute(q)).scalars().all()]

    async def get_recent(self, limit: int = 20) -> List[ActivityLogResponse]:
        q = (
            select(ActivityLog)
            .where(ActivityLog.deleted_at.is_(None))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        items = list((await self.session.execute(q)).scalars().all())
        return [ActivityLogResponse.model_validate(i) for i in items]