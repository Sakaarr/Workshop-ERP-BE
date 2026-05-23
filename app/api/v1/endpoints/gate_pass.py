import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.gate_pass import GatePassCreate, GatePassResponse, GatePassVerify
from app.services.gate_pass_service import GatePassService
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/gate-passes", tags=["Gate Passes"])


@router.get("", response_model=list[GatePassResponse])
async def list_active(_: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await GatePassService(session).list_active()


@router.post("", response_model=GatePassResponse, status_code=201)
async def create_gate_pass(data: GatePassCreate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await GatePassService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-invoice/{invoice_id}", response_model=GatePassResponse | None)
async def get_by_invoice(invoice_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await GatePassService(session).get_by_invoice(invoice_id)


@router.post("/verify", response_model=GatePassResponse)
async def verify_gate_pass(data: GatePassVerify, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await GatePassService(session).verify(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{gate_pass_id}", response_model=GatePassResponse)
async def get_gate_pass(gate_pass_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await GatePassService(session).get(gate_pass_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))