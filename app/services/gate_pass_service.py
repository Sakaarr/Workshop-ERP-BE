import uuid
import random
import string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invoice import GatePass, Invoice
from app.models.job_card import JobCard
from app.models.vehicle import Vehicle
from app.models.customer import Customer
from app.schemas.gate_pass import GatePassCreate, GatePassResponse, GatePassVerify


class GatePassService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: GatePassCreate) -> GatePassResponse:
        # Check invoice is paid or partially paid
        invoice = await self.session.get(Invoice, data.invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.payment_status == "pending":
            raise ValueError("Cannot issue gate pass — invoice is unpaid")

        # Check no existing gate pass
        existing = await self.session.execute(
            select(GatePass).where(GatePass.invoice_id == data.invoice_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Gate pass already issued for this invoice")

        code = self._generate_code()
        gate_pass = GatePass(
            invoice_id=data.invoice_id,
            job_card_id=data.job_card_id,
            verification_code=code,
            notes=data.notes,
        )
        self.session.add(gate_pass)
        await self.session.flush()
        await self.session.refresh(gate_pass)
        return await self._enrich(gate_pass)

    async def get(self, gate_pass_id: uuid.UUID) -> GatePassResponse:
        gp = await self.session.get(GatePass, gate_pass_id)
        if not gp:
            raise ValueError("Gate pass not found")
        return await self._enrich(gp)

    async def get_by_invoice(self, invoice_id: uuid.UUID) -> GatePassResponse | None:
        result = await self.session.execute(
            select(GatePass).where(GatePass.invoice_id == invoice_id)
        )
        gp = result.scalar_one_or_none()
        if not gp:
            return None
        return await self._enrich(gp)

    async def verify(self, data: GatePassVerify) -> GatePassResponse:
        result = await self.session.execute(
            select(GatePass).where(GatePass.verification_code == data.verification_code.upper())
        )
        gp = result.scalar_one_or_none()
        if not gp:
            raise ValueError("Invalid verification code")
        if gp.is_used:
            raise ValueError("Gate pass already used")
        gp.is_used = True
        await self.session.flush()
        return await self._enrich(gp)

    async def list_active(self) -> list[GatePassResponse]:
        result = await self.session.execute(
            select(GatePass).where(GatePass.is_used == False).order_by(GatePass.created_at.desc())
        )
        passes = result.scalars().all()
        return [await self._enrich(gp) for gp in passes]

    def _generate_code(self) -> str:
        chars = string.ascii_uppercase + string.digits
        return "GP-" + "".join(random.choices(chars, k=8))

    async def _enrich(self, gp: GatePass) -> GatePassResponse:
        result = GatePassResponse.model_validate(gp)
        invoice = await self.session.get(Invoice, gp.invoice_id)
        job = await self.session.get(JobCard, gp.job_card_id)
        if invoice:
            result.invoice_number = invoice.invoice_number
            result.total_amount = str(invoice.total_amount)
            result.payment_status = invoice.payment_status
            customer = await self.session.get(Customer, invoice.customer_id)
            if customer:
                result.customer_name = customer.name
        if job:
            result.job_number = job.job_number
            vehicle = await self.session.get(Vehicle, job.vehicle_id)
            if vehicle:
                result.vehicle_plate = vehicle.plate_number
                result.vehicle_brand = vehicle.brand
                result.vehicle_model = vehicle.model
        return result