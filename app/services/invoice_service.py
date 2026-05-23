import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import Invoice, PaymentStatus
from app.models.job_card import JobCard
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.user import User
from app.repositories.invoice import InvoiceRepository
from app.repositories.job_card import JobCardRepository
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    InvoiceListItem, PaymentRecord,
)
from app.schemas.base import PaginatedResponse


class InvoiceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InvoiceRepository(session)
        self.job_repo = JobCardRepository(session)

    async def create_from_job(self, job_card_id: uuid.UUID, data: InvoiceCreate) -> InvoiceResponse:
        # Prevent duplicate invoices
        existing = await self.repo.get_by_job_card(job_card_id)
        if existing:
            raise ValueError("Invoice already exists for this job card")

        job = await self.job_repo.get_or_raise(job_card_id)

        # Calculate parts subtotal
        parts_total = Decimal("0.00")
        for part in job.parts_used:
            parts_total += part.line_total

        subtotal = parts_total + job.labor_charge
        discount = data.discount_amount or Decimal("0.00")
        taxable = subtotal - discount
        tax_rate = data.tax_rate or Decimal("13.00")
        tax_amount = (taxable * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = taxable + tax_amount

        # Determine payment status
        paid = data.paid_amount or Decimal("0.00")
        if paid >= total:
            status = PaymentStatus.PAID
        elif paid > Decimal("0.00"):
            status = PaymentStatus.PARTIAL
        else:
            status = PaymentStatus.PENDING

        invoice_number = await self.repo.get_next_invoice_number()

        invoice = await self.repo.create(
            invoice_number=invoice_number,
            job_card_id=job_card_id,
            customer_id=data.customer_id,
            subtotal=subtotal,
            discount_amount=discount,
            discount_reason=data.discount_reason,
            taxable_amount=taxable,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total,
            paid_amount=paid,
            payment_status=status,
            payment_method=data.payment_method,
            notes=data.notes,
        )
        return await self._enrich(invoice)

    async def record_payment(self, invoice_id: uuid.UUID, data: PaymentRecord) -> InvoiceResponse:
        invoice = await self.repo.get_or_raise(invoice_id)
        new_paid = invoice.paid_amount + data.amount
        if new_paid > invoice.total_amount:
            raise ValueError("Payment exceeds invoice total")
        if new_paid >= invoice.total_amount:
            status = PaymentStatus.PAID
        else:
            status = PaymentStatus.PARTIAL
        updated = await self.repo.update(
            invoice,
            paid_amount=new_paid,
            payment_status=status,
            payment_method=data.payment_method,
        )
        return await self._enrich(updated)

    async def get(self, invoice_id: uuid.UUID) -> InvoiceResponse:
        inv = await self.repo.get_or_raise(invoice_id)
        return await self._enrich(inv)

    async def get_by_job(self, job_card_id: uuid.UUID) -> InvoiceResponse | None:
        inv = await self.repo.get_by_job_card(job_card_id)
        if not inv:
            return None
        return await self._enrich(inv)

    async def list(self, page: int, page_size: int, search: str | None) -> PaginatedResponse[InvoiceListItem]:
        skip = (page - 1) * page_size
        items, total = await self.repo.list(skip=skip, limit=page_size)
        enriched = []
        for inv in items:
            item = InvoiceListItem.model_validate(inv)
            customer = await self.session.get(Customer, inv.customer_id)
            job = await self.session.get(JobCard, inv.job_card_id)
            if customer:
                item.customer_name = customer.name
            if job:
                item.job_number = job.job_number
                vehicle = await self.session.get(Vehicle, job.vehicle_id)
                if vehicle:
                    item.vehicle_plate = vehicle.plate_number
            enriched.append(item)
        return PaginatedResponse(
            items=enriched, total=total, page=page,
            page_size=page_size, pages=max(1, -(-total // page_size)),
        )

    async def update(self, invoice_id: uuid.UUID, data: InvoiceUpdate) -> InvoiceResponse:
        inv = await self.repo.get_or_raise(invoice_id)
        updated = await self.repo.update(inv, **data.model_dump(exclude_none=True))
        return await self._enrich(updated)

    async def _enrich(self, inv: Invoice) -> InvoiceResponse:
        result = InvoiceResponse.model_validate(inv)
        customer = await self.session.get(Customer, inv.customer_id)
        job = await self.session.get(JobCard, inv.job_card_id)
        if customer:
            result.customer_name = customer.name
        if job:
            result.job_number = job.job_number
            vehicle = await self.session.get(Vehicle, job.vehicle_id)
            if vehicle:
                result.vehicle_plate = vehicle.plate_number
        return result