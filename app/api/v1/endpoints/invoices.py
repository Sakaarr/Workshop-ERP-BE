import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListItem, PaymentRecord
from app.schemas.base import PaginatedResponse
from app.services.invoice_service import InvoiceService
from app.api.v1.dependencies.auth import CurrentUser
from app.services.email_service import send_invoice_generated

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=PaginatedResponse[InvoiceListItem])
async def list_invoices(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
):
    return await InvoiceService(session).list(page, page_size, search)


@router.post("/from-job/{job_card_id}", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    job_card_id: uuid.UUID,
    data: InvoiceCreate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        inv = await InvoiceService(session).create_from_job(job_card_id, data)

        from app.models.customer import Customer
        from app.models.job_card import JobCard
        from app.models.vehicle import Vehicle
        import asyncio

        customer = await session.get(Customer, data.customer_id)
        job = await session.get(JobCard, job_card_id)
        vehicle = await session.get(Vehicle, job.vehicle_id) if job else None

        if customer and customer.email:
            asyncio.create_task(send_invoice_generated(
                customer_email=customer.email,
                invoice_number=inv.invoice_number,
                job_number=inv.job_number or "",
                vehicle_plate=inv.vehicle_plate or "",
                subtotal=str(inv.subtotal),
                discount_amount=str(inv.discount_amount),
                tax_rate=str(inv.tax_rate),
                tax_amount=str(inv.tax_amount),
                total_amount=str(inv.total_amount),
                paid_amount=str(inv.paid_amount),
                payment_status=inv.payment_status,
            ))

        return inv
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-job/{job_card_id}", response_model=InvoiceResponse | None)
async def get_invoice_by_job(
    job_card_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await InvoiceService(session).get_by_job(job_card_id)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InvoiceService(session).get(invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InvoiceService(session).update(invoice_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{invoice_id}/payment", response_model=InvoiceResponse)
async def record_payment(
    invoice_id: uuid.UUID,
    data: PaymentRecord,
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await InvoiceService(session).record_payment(invoice_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))