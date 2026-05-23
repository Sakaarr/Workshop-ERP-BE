from pydantic import EmailStr, field_validator
from app.schemas.base import APIBase
from app.models.user import UserRole
import uuid
from datetime import datetime


class LoginRequest(APIBase):
    email: EmailStr
    password: str


class TokenResponse(APIBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(APIBase):
    refresh_token: str


class UserCreate(APIBase):
    full_name: str
    email: EmailStr
    phone: str | None = None
    password: str
    role: UserRole = UserRole.STAFF

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(APIBase):
    full_name: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(APIBase):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    avatar_url: str | None
    created_at: datetime