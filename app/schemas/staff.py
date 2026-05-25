import uuid
from datetime import datetime
from app.schemas.base import APIBase
from app.models.user import UserRole


class StaffCreate(APIBase):
    full_name: str
    email: str
    phone: str | None = None
    role: UserRole = UserRole.STAFF
    password: str


class StaffUpdate(APIBase):
    full_name: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class ProfileUpdate(APIBase):
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None


class StaffResponse(APIBase):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    avatar_url: str | None
    created_at: datetime
    job_count: int = 0


class PasswordChange(APIBase):
    current_password: str
    new_password: str


class AdminPasswordReset(APIBase):
    new_password: str