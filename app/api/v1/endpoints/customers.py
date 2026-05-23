import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListItem
from app.schemas.base import PaginatedResponse
from app.services.customer_service import CustomerService
from app.api.v1.dependencies.auth import CurrentUser

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse[CustomerListItem])
async def list_customers(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
):
    return await CustomerService(session).list(page, page_size, search)


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await CustomerService(session).create(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await CustomerService(session).get(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: uuid.UUID, data: CustomerUpdate, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await CustomerService(session).update(customer_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: uuid.UUID, _: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await CustomerService(session).delete(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))