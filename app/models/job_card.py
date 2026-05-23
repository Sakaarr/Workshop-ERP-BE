import enum
import uuid
from decimal import Decimal
from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class JobStatus(str, enum.Enum):
    WAITING = "waiting"
    DIAGNOSING = "diagnosing"
    REPAIRING = "repairing"
    WAITING_PARTS = "waiting_parts"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class JobCard(BaseModel):
    __tablename__ = "job_cards"

    job_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.WAITING, nullable=False, index=True
    )
    complaint: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    odometer_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    odometer_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    labor_charge: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    delivered_at: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="job_cards")  # type: ignore[name-defined]
    customer: Mapped["Customer"] = relationship("Customer", back_populates="job_cards")  # type: ignore[name-defined]
    assigned_to_user: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="assigned_jobs", foreign_keys=[assigned_to]
    )
    parts_used: Mapped[list["JobCardPart"]] = relationship(  # type: ignore[name-defined]
        "JobCardPart", back_populates="job_card", cascade="all, delete-orphan"
    )
    invoice: Mapped["Invoice | None"] = relationship(  # type: ignore[name-defined]
        "Invoice", back_populates="job_card", uselist=False
    )

    def __repr__(self) -> str:
        return f"<JobCard {self.job_number} [{self.status}]>"