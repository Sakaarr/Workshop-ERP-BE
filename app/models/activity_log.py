import uuid
from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # e.g. "customer.created", "job_card.status_changed", "user.login"

    resource_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )

    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    resource_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    extra_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)