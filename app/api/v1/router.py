from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, customers, vehicles, job_cards,
    invoices, daybook, inventory, gate_pass, pdf,
    analytics, staff, permissions, suppliers, activity_logs,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(vehicles.router)
api_router.include_router(job_cards.router)
api_router.include_router(invoices.router)
api_router.include_router(daybook.router)
api_router.include_router(inventory.router)
api_router.include_router(suppliers.router)
api_router.include_router(gate_pass.router)
api_router.include_router(pdf.router)
api_router.include_router(analytics.router)
api_router.include_router(staff.router)
api_router.include_router(permissions.router)
api_router.include_router(activity_logs.router)