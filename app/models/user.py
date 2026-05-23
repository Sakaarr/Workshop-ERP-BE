import enum
from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STAFF = "staff"


class User(BaseModel):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.STAFF, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    assigned_jobs: Mapped[list["JobCard"]] = relationship(  # type: ignore[name-defined]
        "JobCard", back_populates="assigned_to_user", foreign_keys="JobCard.assigned_to"
    )
    daybook_entries: Mapped[list["DayBookEntry"]] = relationship(  # type: ignore[name-defined]
        "DayBookEntry", back_populates="created_by_user"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"