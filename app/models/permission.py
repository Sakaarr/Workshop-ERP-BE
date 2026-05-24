import uuid
from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


# All available module permissions
AVAILABLE_PERMISSIONS = [
    "dashboard.view",
    "customers.view", "customers.create", "customers.edit", "customers.delete",
    "vehicles.view", "vehicles.create", "vehicles.edit", "vehicles.delete",
    "jobs.view", "jobs.create", "jobs.edit", "jobs.delete", "jobs.change_status",
    "billing.view", "billing.create", "billing.edit", "billing.record_payment",
    "inventory.view", "inventory.create", "inventory.edit", "inventory.delete", "inventory.adjust_stock",
    "suppliers.view", "suppliers.create", "suppliers.edit", "suppliers.delete",
    "daybook.view", "daybook.create", "daybook.delete",
    "gate_pass.view", "gate_pass.create", "gate_pass.verify",
    "reports.view",
    "staff.view", "staff.create", "staff.edit",
    "settings.view",
]

MODULE_PERMISSIONS = {
    "Dashboard":  ["dashboard.view"],
    "Customers":  ["customers.view", "customers.create", "customers.edit", "customers.delete"],
    "Vehicles":   ["vehicles.view", "vehicles.create", "vehicles.edit", "vehicles.delete"],
    "Job Cards":  ["jobs.view", "jobs.create", "jobs.edit", "jobs.delete", "jobs.change_status"],
    "Billing":    ["billing.view", "billing.create", "billing.edit", "billing.record_payment"],
    "Inventory":  ["inventory.view", "inventory.create", "inventory.edit", "inventory.delete", "inventory.adjust_stock"],
    "Suppliers":  ["suppliers.view", "suppliers.create", "suppliers.edit", "suppliers.delete"],
    "Day Book":   ["daybook.view", "daybook.create", "daybook.delete"],
    "Gate Pass":  ["gate_pass.view", "gate_pass.create", "gate_pass.verify"],
    "Reports":    ["reports.view"],
    "Staff":      ["staff.view", "staff.create", "staff.edit"],
    "Settings":   ["settings.view"],
}


class StaffPermission(BaseModel):
    __tablename__ = "staff_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "permission", name="uq_staff_permission"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)