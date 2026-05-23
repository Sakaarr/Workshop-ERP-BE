import uuid
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Supplier(BaseModel):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    pan_vat: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    parts: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="supplier"
    )


class InventoryItem(BaseModel):
    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    part_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="piece", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    supplier: Mapped["Supplier | None"] = relationship("Supplier", back_populates="parts")
    job_uses: Mapped[list["JobCardPart"]] = relationship(
        "JobCardPart", back_populates="item"
    )

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold


class JobCardPart(BaseModel):
    __tablename__ = "job_card_parts"

    job_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    job_card: Mapped["JobCard"] = relationship("JobCard", back_populates="parts_used")  # type: ignore[name-defined]
    item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="job_uses")

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity) - self.discount_amount