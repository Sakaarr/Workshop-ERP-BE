import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class FuelType(str, enum.Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"
    OTHER = "other"


class Vehicle(BaseModel):
    __tablename__ = "vehicles"

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    vin: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    engine_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType), default=FuelType.PETROL, nullable=False
    )
    last_odometer: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # relationships
    customer: Mapped["Customer"] = relationship(  # type: ignore[name-defined]
        "Customer", back_populates="vehicles"
    )
    job_cards: Mapped[list["JobCard"]] = relationship(  # type: ignore[name-defined]
        "JobCard", back_populates="vehicle"
    )

    def __repr__(self) -> str:
        return f"<Vehicle {self.plate_number} — {self.brand} {self.model}>"

