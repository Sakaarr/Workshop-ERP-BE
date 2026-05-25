from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.analytics import DashboardStats, RevenueChartPoint, JobStatusChartPoint, TopCustomer
from app.services.analytics_service import AnalyticsService
from app.api.v1.dependencies.auth import CurrentUser
from app.schemas.analytics import DashboardStats, RevenueChartPoint, JobStatusChartPoint, TopCustomer
from app.schemas.base import APIBase
from decimal import Decimal
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(_: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await AnalyticsService(session).get_dashboard_stats()


@router.get("/revenue-chart", response_model=list[RevenueChartPoint])
async def revenue_chart(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=30, ge=7, le=90),
):
    return await AnalyticsService(session).get_revenue_chart(days)


@router.get("/job-status-chart", response_model=list[JobStatusChartPoint])
async def job_status_chart(_: CurrentUser, session: Annotated[AsyncSession, Depends(get_db)]):
    return await AnalyticsService(session).get_job_status_chart()


@router.get("/top-customers", response_model=list[TopCustomer])
async def top_customers(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=5, ge=1, le=20),
):
    return await AnalyticsService(session).get_top_customers(limit)


class SupplierPartStat(APIBase):
    supplier_id: str
    supplier_name: str
    parts_count: int
    total_stock_value: Decimal


@router.get("/supplier-parts", response_model=list[SupplierPartStat])
async def supplier_parts_stats(
    _: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy import select, func
    from app.models.inventory import InventoryItem, Supplier

    q = (
        select(
            Supplier.id,
            Supplier.name,
            func.count(InventoryItem.id).label("parts_count"),
            func.coalesce(
                func.sum(InventoryItem.quantity * InventoryItem.cost_price), 0
            ).label("total_stock_value"),
        )
        .join(InventoryItem, InventoryItem.supplier_id == Supplier.id)
        .where(
            Supplier.deleted_at.is_(None),
            InventoryItem.deleted_at.is_(None),
        )
        .group_by(Supplier.id, Supplier.name)
        .order_by(func.count(InventoryItem.id).desc())
        .limit(10)
    )
    rows = (await session.execute(q)).all()
    return [
        SupplierPartStat(
            supplier_id=str(r.id),
            supplier_name=r.name,
            parts_count=r.parts_count,
            total_stock_value=Decimal(str(r.total_stock_value)),
        )
        for r in rows
    ]