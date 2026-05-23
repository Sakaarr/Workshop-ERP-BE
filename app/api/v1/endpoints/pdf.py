import uuid
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.invoice import Invoice, GatePass
from app.models.job_card import JobCard
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.services.pdf_service import generate_invoice_pdf, generate_gate_pass_pdf, generate_job_card_pdf
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/pdf", tags=["PDF"])


@router.get("/invoice/{invoice_id}")
async def download_invoice(
    invoice_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    job = await session.get(JobCard, invoice.job_card_id)
    customer = await session.get(Customer, invoice.customer_id)
    vehicle = await session.get(Vehicle, job.vehicle_id) if job else None

    items = []
    if job:
        if job.labor_charge > 0:
            items.append({"description": "Labour Charge", "quantity": 1, "unit_price": str(job.labor_charge), "total": str(job.labor_charge)})
        for part in job.parts_used:
            items.append({
                "description": part.item.name if part.item else "Part",
                "quantity": part.quantity,
                "unit_price": str(part.unit_price),
                "total": str(part.line_total),
            })

    pdf_data = {
        "invoice_number": invoice.invoice_number,
        "date": invoice.created_at.strftime("%Y-%m-%d"),
        "job_number": job.job_number if job else "",
        "vehicle_plate": vehicle.plate_number if vehicle else "",
        "vehicle_name": f"{vehicle.brand} {vehicle.model}" if vehicle else "",
        "customer_name": customer.name if customer else "",
        "customer_phone": customer.phone_primary if customer else "",
        "customer_address": customer.address if customer else "",
        "items": items,
        "subtotal": str(invoice.subtotal),
        "discount_amount": str(invoice.discount_amount),
        "discount_reason": invoice.discount_reason or "",
        "tax_rate": str(invoice.tax_rate),
        "tax_amount": str(invoice.tax_amount),
        "total_amount": str(invoice.total_amount),
        "paid_amount": str(invoice.paid_amount),
        "payment_status": invoice.payment_status,
        "payment_method": invoice.payment_method or "",
        "notes": invoice.notes or "",
    }

    pdf_bytes = generate_invoice_pdf(pdf_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{invoice.invoice_number}.pdf"'},
    )


@router.get("/gate-pass/{gate_pass_id}")
async def download_gate_pass(
    gate_pass_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    gp = await session.get(GatePass, gate_pass_id)
    if not gp:
        raise HTTPException(status_code=404, detail="Gate pass not found")

    invoice = await session.get(Invoice, gp.invoice_id)
    job = await session.get(JobCard, gp.job_card_id)
    customer = await session.get(Customer, invoice.customer_id) if invoice else None
    vehicle = await session.get(Vehicle, job.vehicle_id) if job else None

    pdf_data = {
        "verification_code": gp.verification_code,
        "issued_at": gp.created_at.strftime("%Y-%m-%d %H:%M"),
        "customer_name": customer.name if customer else "",
        "vehicle_plate": vehicle.plate_number if vehicle else "",
        "vehicle_brand": vehicle.brand if vehicle else "",
        "vehicle_model": vehicle.model if vehicle else "",
        "job_number": job.job_number if job else "",
        "invoice_number": invoice.invoice_number if invoice else "",
        "total_amount": str(invoice.total_amount) if invoice else "0.00",
        "payment_status": invoice.payment_status if invoice else "",
        "notes": gp.notes or "",
    }

    pdf_bytes = generate_gate_pass_pdf(pdf_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="gate-pass-{gp.verification_code}.pdf"'},
    )


@router.get("/job-card/{job_card_id}")
async def download_job_card(
    job_card_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    job = await session.get(JobCard, job_card_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job card not found")

    customer = await session.get(Customer, job.customer_id)
    vehicle = await session.get(Vehicle, job.vehicle_id)

    pdf_data = {
        "job_number": job.job_number,
        "status": job.status,
        "date": job.created_at.strftime("%Y-%m-%d"),
        "customer_name": customer.name if customer else "",
        "customer_phone": customer.phone_primary if customer else "",
        "vehicle_plate": vehicle.plate_number if vehicle else "",
        "vehicle_name": f"{vehicle.brand} {vehicle.model}" if vehicle else "",
        "odometer_in": job.odometer_in,
        "complaint": job.complaint,
        "diagnosis": job.diagnosis or "",
        "estimated_cost": str(job.estimated_cost),
        "labor_charge": str(job.labor_charge),
    }

    pdf_bytes = generate_job_card_pdf(pdf_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{job.job_number}.pdf"'},
    )