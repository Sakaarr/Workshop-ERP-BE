import os
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Graceful fallback if fastapi-mail not installed
try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
    MAIL_AVAILABLE = True
except ImportError:
    MAIL_AVAILABLE = False

from app.core.config import settings
import structlog

logger = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def _get_mail_config():
    if not MAIL_AVAILABLE:
        return None
    if not getattr(settings, "SMTP_HOST", None):
        return None
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.EMAILS_FROM_EMAIL,
        MAIL_FROM_NAME="Auto Garden Pvt. Ltd.",
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=str(TEMPLATES_DIR),
    )


async def send_email(
    to: str | list[str],
    subject: str,
    template_name: str,
    context: dict[str, Any],
) -> bool:
    """
    Send an email using a Jinja2 template.
    Falls back to logging if SMTP not configured.
    """
    recipients = [to] if isinstance(to, str) else to
    ctx = {
        "subject": subject,
        "business_phone": settings.BUSINESS_PHONE,
        "business_name": settings.BUSINESS_NAME,
        **context,
    }

    html_body = _render_template(template_name, ctx)

    config = _get_mail_config()
    if not config:
        logger.info(
            "Email not sent — SMTP not configured",
            to=recipients,
            subject=subject,
            template=template_name,
        )
        return False

    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html_body,
            subtype=MessageType.html,
        )
        fm = FastMail(config)
        await fm.send_message(message)
        logger.info("Email sent", to=recipients, subject=subject)
        return True
    except Exception as e:
        logger.error("Email send failed", error=str(e), to=recipients)
        return False


# ── Convenience functions ──────────────────────────────────

async def send_job_card_created(
    customer_email: str,
    customer_name: str,
    job_number: str,
    vehicle_plate: str,
    vehicle_name: str,
    complaint: str,
    odometer_in: int,
    assigned_to: str | None = None,
) -> bool:
    return await send_email(
        to=customer_email,
        subject=f"Job Card {job_number} Created — Auto Garden",
        template_name="job_card_created.html",
        context=dict(
            customer_name=customer_name,
            job_number=job_number,
            vehicle_plate=vehicle_plate,
            vehicle_name=vehicle_name,
            complaint=complaint,
            odometer_in=odometer_in,
            assigned_to=assigned_to,
        ),
    )


STATUS_LABELS = {
    "waiting":       ("Waiting",          "badge-amber"),
    "diagnosing":    ("Diagnosing",        "badge-blue"),
    "repairing":     ("Under Repair",      "badge-blue"),
    "waiting_parts": ("Awaiting Parts",    "badge-amber"),
    "ready":         ("Ready for Pickup",  "badge-green"),
    "delivered":     ("Delivered",         "badge-green"),
}


async def send_job_status_changed(
    customer_email: str,
    job_number: str,
    vehicle_plate: str,
    new_status: str,
    notes: str | None = None,
) -> bool:
    label, badge = STATUS_LABELS.get(new_status, (new_status, "badge-amber"))
    return await send_email(
        to=customer_email,
        subject=f"Vehicle Update: {label} — {job_number}",
        template_name="job_status_changed.html",
        context=dict(
            job_number=job_number,
            vehicle_plate=vehicle_plate,
            status=new_status,
            status_label=label,
            status_badge_class=badge,
            notes=notes,
        ),
    )


async def send_invoice_generated(
    customer_email: str,
    invoice_number: str,
    job_number: str,
    vehicle_plate: str,
    subtotal: str,
    discount_amount: str,
    tax_rate: str,
    tax_amount: str,
    total_amount: str,
    paid_amount: str,
    payment_status: str,
) -> bool:
    balance = float(total_amount) - float(paid_amount)
    return await send_email(
        to=customer_email,
        subject=f"Invoice {invoice_number} — Auto Garden",
        template_name="invoice_generated.html",
        context=dict(
            invoice_number=invoice_number,
            job_number=job_number,
            vehicle_plate=vehicle_plate,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=paid_amount,
            payment_status=payment_status,
            balance_due=f"{balance:.2f}",
        ),
    )


async def send_gate_pass_issued(
    customer_email: str,
    customer_name: str,
    verification_code: str,
    vehicle_plate: str,
    vehicle_name: str,
    invoice_number: str,
    total_amount: str,
) -> bool:
    return await send_email(
        to=customer_email,
        subject=f"Gate Pass {verification_code} — Auto Garden",
        template_name="gate_pass_issued.html",
        context=dict(
            customer_name=customer_name,
            verification_code=verification_code,
            vehicle_plate=vehicle_plate,
            vehicle_name=vehicle_name,
            invoice_number=invoice_number,
            total_amount=total_amount,
        ),
    )


async def send_low_stock_alert(
    admin_emails: list[str],
    items: list[dict],
) -> bool:
    return await send_email(
        to=admin_emails,
        subject=f"⚠️ Low Stock Alert — {len(items)} items need restocking",
        template_name="low_stock_alert.html",
        context=dict(items=items, count=len(items)),
    )


async def send_welcome_staff(
    email: str,
    full_name: str,
    role: str,
    temp_password: str,
    login_url: str = "https://autogarden.com.np/login",
) -> bool:
    return await send_email(
        to=email,
        subject="Welcome to Auto Garden — Your Account Details",
        template_name="welcome_staff.html",
        context=dict(
            full_name=full_name,
            email=email,
            role=role.replace("_", " ").title(),
            temp_password=temp_password,
            login_url=login_url,
        ),
    )