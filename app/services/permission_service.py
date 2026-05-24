import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.permission import StaffPermission, AVAILABLE_PERMISSIONS
from app.models.user import User, UserRole


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[str]:
        """Super admin and admin get ALL permissions automatically."""
        user = await self.session.get(User, user_id)
        if not user:
            return []
        if user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            return AVAILABLE_PERMISSIONS

        q = select(StaffPermission).where(
            StaffPermission.user_id == user_id,
            StaffPermission.granted == True,
            StaffPermission.deleted_at.is_(None),
        )
        perms = (await self.session.execute(q)).scalars().all()
        return [p.permission for p in perms]

    async def set_user_permissions(self, user_id: uuid.UUID, permissions: list[str]) -> list[str]:
        """Replace all permissions for a staff user."""
        # Validate
        invalid = [p for p in permissions if p not in AVAILABLE_PERMISSIONS]
        if invalid:
            raise ValueError(f"Invalid permissions: {invalid}")

        # Delete existing
        await self.session.execute(
            delete(StaffPermission).where(StaffPermission.user_id == user_id)
        )
        await self.session.flush()

        # Insert new
        for perm in permissions:
            sp = StaffPermission(user_id=user_id, permission=perm, granted=True)
            self.session.add(sp)

        await self.session.flush()
        return permissions

    async def has_permission(self, user_id: uuid.UUID, permission: str) -> bool:
        perms = await self.get_user_permissions(user_id)
        return permission in perms

    async def check_permission(self, user: User, permission: str) -> None:
        """Raise ValueError if user lacks permission."""
        if user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            return
        has = await self.has_permission(user.id, permission)
        if not has:
            raise PermissionError(f"Access denied: missing permission '{permission}'")