from decimal import Decimal
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    phone_primary: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    phone_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pan_vat: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outstanding_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    # relationships
    vehicles: Mapped[list["Vehicle"]] = relationship(  # type: ignore[name-defined]
        "Vehicle", back_populates="customer", cascade="all, delete-orphan"
    )
    job_cards: Mapped[list["JobCard"]] = relationship(  # type: ignore[name-defined]
        "JobCard", back_populates="customer"
    )
    invoices: Mapped[list["Invoice"]] = relationship(  # type: ignore[name-defined]
        "Invoice", back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name} [{self.phone_primary}]>"