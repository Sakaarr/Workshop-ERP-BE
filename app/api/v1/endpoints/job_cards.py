import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.job_card import JobStatus
from app.models.user import User, UserRole
from app.schemas.job_card import (
    JobCardCreate, JobCardUpdate, JobCardResponse,
    JobCardListItem, JobCardStatusUpdate,
)
from app.schemas.base import PaginatedResponse, BulkDeleteRequest
from app.services.job_card_service import JobCardService
from app.api.v1.dependencies.auth import require_permission, CurrentUser
from app.schemas.staff import StaffResponse
from app.services.email_service import send_job_card_created, send_job_status_changed

router = APIRouter(prefix="/job-cards", tags=["Job Cards"])

ViewJob        = Annotated[User, Depends(require_permission("jobs.view"))]
CreateJob      = Annotated[User, Depends(require_permission("jobs.create"))]
EditJob        = Annotated[User, Depends(require_permission("jobs.edit"))]
DeleteJob      = Annotated[User, Depends(require_permission("jobs.delete"))]
ChangeStatus   = Annotated[User, Depends(require_permission("jobs.change_status"))]


@router.get("", response_model=PaginatedResponse[JobCardListItem])
async def list_jobs(
    _: ViewJob,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: JobStatus | None = Query(default=None),
):
    return await JobCardService(session).list(page, page_size, search, status)


@router.get("/assignable-staff", response_model=list[StaffResponse])
async def get_assignable_staff(
    _: ViewJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Return all active staff members who can be assigned to jobs."""
    from sqlalchemy import select, func
    from app.models.job_card import JobCard

    q = select(User).where(
        User.deleted_at.is_(None),
        User.is_active == True,
    ).order_by(User.full_name)
    users = list((await session.execute(q)).scalars().all())

    result = []
    for u in users:
        count_q = select(func.count()).select_from(JobCard).where(
            JobCard.assigned_to == u.id,
            JobCard.deleted_at.is_(None),
            JobCard.status.notin_([JobStatus.DELIVERED, JobStatus.CANCELLED]),
        )
        active_count = (await session.execute(count_q)).scalar_one()
        from app.schemas.staff import StaffResponse
        sr = StaffResponse.model_validate(u)
        sr.job_count = active_count
        result.append(sr)
    return result


@router.post("", response_model=JobCardResponse, status_code=201)
async def create_job(
    data: JobCardCreate,
    _: CreateJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        job = await JobCardService(session).create(data)

        # Fire email notification
        from app.models.customer import Customer
        from app.models.vehicle import Vehicle
        from app.models.user import User as UserModel
        import asyncio

        customer = await session.get(Customer, data.customer_id)
        vehicle = await session.get(Vehicle, data.vehicle_id)
        assigned_user = await session.get(UserModel, data.assigned_to) if data.assigned_to else None

        if customer and customer.email:
            asyncio.create_task(send_job_card_created(
                customer_email=customer.email,
                customer_name=customer.name,
                job_number=job.job_number,
                vehicle_plate=vehicle.plate_number if vehicle else "",
                vehicle_name=f"{vehicle.brand} {vehicle.model}" if vehicle else "",
                complaint=data.complaint,
                odometer_in=data.odometer_in,
                assigned_to=assigned_user.full_name if assigned_user else None,
            ))

        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}", response_model=JobCardResponse)
async def get_job(
    job_id: uuid.UUID,
    _: ViewJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await JobCardService(session).get(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{job_id}", response_model=JobCardResponse)
async def update_job(
    job_id: uuid.UUID,
    data: JobCardUpdate,
    _: EditJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await JobCardService(session).update(job_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{job_id}/status", response_model=JobCardResponse)
async def update_status(
    job_id: uuid.UUID,
    data: JobCardStatusUpdate,
    _: ChangeStatus,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        job = await JobCardService(session).update_status(job_id, data)

        from app.models.customer import Customer
        from app.models.vehicle import Vehicle
        import asyncio

        customer = await session.get(Customer, job.customer_id)
        vehicle = await session.get(Vehicle, job.vehicle_id)

        if customer and customer.email:
            asyncio.create_task(send_job_status_changed(
                customer_email=customer.email,
                job_number=job.job_number,
                vehicle_plate=vehicle.plate_number if vehicle else "",
                new_status=data.status.value,
                notes=data.notes,
            ))

        return job
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: uuid.UUID,
    _: DeleteJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await JobCardService(session).delete(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk-delete", status_code=204)
async def bulk_delete_jobs(
    data: BulkDeleteRequest,
    _: DeleteJob,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await JobCardService(session).bulk_delete(data.ids)
