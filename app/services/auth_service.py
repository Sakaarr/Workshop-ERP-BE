import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated. Contact admin.")

        return TokenResponse(
            access_token=create_access_token(
                subject=user.id,
                extra_claims={"role": user.role, "name": user.full_name},
            ),
            refresh_token=create_refresh_token(subject=user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, KeyError, ValueError) as e:
            raise ValueError("Invalid or expired refresh token") from e

        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        return TokenResponse(
            access_token=create_access_token(
                subject=user.id,
                extra_claims={"role": user.role, "name": user.full_name},
            ),
            refresh_token=create_refresh_token(subject=user.id),
        )

    async def create_user(self, data: UserCreate) -> UserResponse:
        existing = await self._get_user_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email} is already registered")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return UserResponse.model_validate(user)

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_current_user(self, token: str) -> User:
        try:
            payload = decode_token(token)
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, KeyError, ValueError) as e:
            raise ValueError("Invalid token") from e

        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")
        return user