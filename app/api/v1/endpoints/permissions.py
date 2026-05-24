import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.models.permission import AVAILABLE_PERMISSIONS, MODULE_PERMISSIONS
from app.services.permission_service import PermissionService
from app.api.v1.dependencies.auth import CurrentUser, AdminUser

router = APIRouter(prefix="/permissions", tags=["Permissions"])


class SetPermissionsRequest(BaseModel):
    permissions: list[str]


@router.get("/available")
async def get_available(_: CurrentUser):
    return {"permissions": AVAILABLE_PERMISSIONS, "modules": MODULE_PERMISSIONS}


@router.get("/user/{user_id}")
async def get_user_permissions(
    user_id: uuid.UUID,
    _: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    perms = await PermissionService(session).get_user_permissions(user_id)
    return {"permissions": perms}


@router.get("/me")
async def get_my_permissions(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    perms = await PermissionService(session).get_user_permissions(current_user.id)
    return {"permissions": perms}


@router.put("/user/{user_id}")
async def set_user_permissions(
    user_id: uuid.UUID,
    data: SetPermissionsRequest,
    _: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        perms = await PermissionService(session).set_user_permissions(user_id, data.permissions)
        return {"permissions": perms}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))