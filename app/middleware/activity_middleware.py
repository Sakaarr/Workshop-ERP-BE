from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
import time

# Action mapping: (method, path_pattern) → (action, resource_type)
ACTION_MAP = [
    # Auth
    ("POST", "/auth/login",    "user.login",    "user"),
    ("POST", "/auth/refresh",  "user.token_refresh", "user"),

    # Customers
    ("POST",   "/customers",       "customer.created", "customer"),
    ("PATCH",  "/customers/",      "customer.updated", "customer"),
    ("DELETE", "/customers/",      "customer.deleted", "customer"),

    # Vehicles
    ("POST",   "/vehicles",        "vehicle.created", "vehicle"),
    ("PATCH",  "/vehicles/",       "vehicle.updated", "vehicle"),
    ("DELETE", "/vehicles/",       "vehicle.deleted", "vehicle"),

    # Job cards
    ("POST",   "/job-cards",       "job_card.created",        "job_card"),
    ("PATCH",  "/job-cards/",      "job_card.updated",        "job_card"),
    ("DELETE", "/job-cards/",      "job_card.deleted",        "job_card"),
    ("PATCH",  "/status",          "job_card.status_changed", "job_card"),

    # Invoices
    ("POST",   "/invoices/from-job", "invoice.created",          "invoice"),
    ("POST",   "/payment",           "invoice.payment_recorded", "invoice"),

    # Inventory
    ("POST",   "/inventory",         "inventory.part_added",     "inventory"),
    ("PATCH",  "/inventory/",        "inventory.part_updated",   "inventory"),
    ("DELETE", "/inventory/",        "inventory.part_deleted",   "inventory"),
    ("POST",   "/adjust-stock",      "inventory.stock_adjusted", "inventory"),

    # Gate pass
    ("POST",   "/gate-passes",       "gate_pass.issued",   "gate_pass"),
    ("POST",   "/gate-passes/verify","gate_pass.verified", "gate_pass"),

    # Staff
    ("POST",   "/staff",            "staff.created",          "staff"),
    ("PATCH",  "/staff/",           "staff.updated",          "staff"),
    ("DELETE", "/staff/",           "staff.deleted",          "staff"),
    ("POST",   "/reset-password",   "staff.password_reset",   "staff"),

    # Day book
    ("POST",   "/daybook",          "daybook.entry_created",  "daybook"),
    ("DELETE", "/daybook/",         "daybook.entry_deleted",  "daybook"),
]


def _match_action(method: str, path: str) -> tuple[str, str] | None:
    for m, p, action, resource in ACTION_MAP:
        if method == m and p in path:
            return action, resource
    return None


class ActivityLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Only log successful mutating requests
        if response.status_code not in (200, 201, 204):
            return response

        path = request.url.path
        method = request.method

        # Skip non-API and GET requests
        if not path.startswith("/api/v1") or method == "GET":
            return response

        match = _match_action(method, path)
        if not match:
            return response

        action, resource_type = match

        # Fire-and-forget log (don't block response)
        try:
            from app.core.database import AsyncSessionFactory
            from app.core.security import decode_token
            from app.models.user import User as UserModel

            token = request.headers.get("authorization", "").replace("Bearer ", "")
            user = None
            if token:
                try:
                    import uuid
                    payload = decode_token(token)
                    user_id = uuid.UUID(payload["sub"])
                    async with AsyncSessionFactory() as session:
                        user = await session.get(UserModel, user_id)
                        if user:
                            from app.services.activity_log_service import ActivityLogService
                            svc = ActivityLogService(session)
                            path_parts = path.split("/")
                            resource_id = None
                            for part in path_parts:
                                try:
                                    uuid.UUID(part)
                                    resource_id = part
                                    break
                                except Exception:
                                    pass

                            await svc.log(
                                action=action,
                                description=f"{user.full_name} performed {action.replace('_', ' ').replace('.', ' ')}",
                                user=user,
                                resource_type=resource_type,
                                resource_id=resource_id,
                                ip_address=request.client.host if request.client else None,
                                user_agent=request.headers.get("user-agent", ""),
                            )
                            await session.commit()
                except Exception:
                    pass
        except Exception:
            pass

        return response