import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.job_card import JobCard
from app.schemas.staff import StaffCreate, StaffUpdate, StaffResponse, PasswordChange, AdminPasswordReset, ProfileUpdate
from app.schemas.base import PaginatedResponse, BulkDeleteRequest
from app.services.auth_service import AuthService
from app.core.security import hash_password, verify_password
from app.api.v1.dependencies.auth import CurrentUser, AdminUser, require_super_admin
from app.services.email_service import send_welcome_staff

router = APIRouter(prefix="/staff", tags=["Staff"])


async def _enrich(user: User, session: AsyncSession) -> StaffResponse:
    q = select(func.count()).select_from(JobCard).where(
        JobCard.assigned_to == user.id,
        JobCard.deleted_at.is_(None),
    )
    count = (await session.execute(q)).scalar_one()
    result = StaffResponse.model_validate(user)
    result.job_count = count
    return result


@router.get("", response_model=PaginatedResponse[StaffResponse])
async def list_staff(
    _: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20),
    search: str | None = Query(default=None),
):
    skip = (page - 1) * page_size
    base = [User.deleted_at.is_(None)]
    if search:
        from sqlalchemy import or_
        base.append(or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    count_q = select(func.count()).select_from(User).where(*base)
    total = (await session.execute(count_q)).scalar_one()

    items_q = select(User).where(*base).offset(skip).limit(page_size).order_by(User.created_at.desc())
    users = list((await session.execute(items_q)).scalars().all())
    enriched = [await _enrich(u, session) for u in users]

    return PaginatedResponse(
        items=enriched, total=total, page=page,
        page_size=page_size, pages=max(1, -(-total // page_size)),
    )


@router.post("", response_model=StaffResponse, status_code=201)
async def create_staff(data: StaffCreate, _: AdminUser, session: Annotated[AsyncSession, Depends(get_db)]):
    from app.schemas.auth import UserCreate
    import asyncio
    try:
        user_resp = await AuthService(session).create_user(
            UserCreate(full_name=data.full_name, email=data.email,
                       phone=data.phone, password=data.password, role=data.role)
        )
        user = await session.get(User, user_resp.id)

        asyncio.create_task(send_welcome_staff(
            email=data.email,
            full_name=data.full_name,
            role=data.role,
            temp_password=data.password,
        ))

        return await _enrich(user, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=StaffResponse)
async def get_my_profile(current_user: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await _enrich(current_user, session)


@router.patch("/me/profile", response_model=StaffResponse)
async def update_my_profile(
    data: ProfileUpdate,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, key, value)
    await session.flush()
    return await _enrich(current_user, session)

@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(staff_id: uuid.UUID, _: AdminUser, session: Annotated[AsyncSession, Depends(get_db)]):
    user = await session.get(User, staff_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return await _enrich(user, session)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(staff_id: uuid.UUID, data: StaffUpdate, _: AdminUser, session: Annotated[AsyncSession, Depends(get_db)]):
    user = await session.get(User, staff_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=404, detail="Staff member not found")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(user, key, value)
    await session.flush()
    return await _enrich(user, session)


@router.post("/{staff_id}/reset-password", status_code=204)
async def reset_password(staff_id: uuid.UUID, data: AdminPasswordReset, _: Annotated[User, Depends(require_super_admin)], session: Annotated[AsyncSession, Depends(get_db)]):
    user = await session.get(User, staff_id)
    if not user:
        raise HTTPException(status_code=404, detail="Staff not found")
    user.hashed_password = hash_password(data.new_password)
    await session.flush()


@router.post("/me/change-password", status_code=204)
async def change_password(data: PasswordChange, current_user: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    current_user.hashed_password = hash_password(data.new_password)
    await session.flush()


@router.delete("/{staff_id}", status_code=204)
async def delete_staff(staff_id: uuid.UUID, current_user: Annotated[User, Depends(require_super_admin)], session: Annotated[AsyncSession, Depends(get_db)]):
    user = await session.get(User, staff_id)
    if not user:
        raise HTTPException(status_code=404, detail="Staff not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    from datetime import datetime, timezone
    user.deleted_at = datetime.now(timezone.utc)
    await session.flush()


@router.post("/bulk-delete", status_code=204)
async def bulk_delete_staff(
    data: BulkDeleteRequest,
    current_user: Annotated[User, Depends(require_super_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    from datetime import datetime, timezone

    for staff_id in data.ids:
        user = await session.get(User, staff_id)
        if not user:
            continue
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        user.deleted_at = datetime.now(timezone.utc)
    await session.flush()
