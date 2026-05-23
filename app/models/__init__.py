# Import all models here so SQLAlchemy and Alembic can discover them
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.vehicle import Vehicle, FuelType
from app.models.job_card import JobCard, JobStatus
from app.models.inventory import InventoryItem, Supplier
from app.models.invoice import Invoice, GatePass, DayBookEntry, PaymentStatus, PaymentMethod

__all__ = [
    "User", "UserRole",
    "Customer",
    "Vehicle", "FuelType",
    "JobCard", "JobStatus", "JobCardPart",
    "InventoryItem", "Supplier",
    "Invoice", "GatePass", "DayBookEntry", "PaymentStatus", "PaymentMethod",
]