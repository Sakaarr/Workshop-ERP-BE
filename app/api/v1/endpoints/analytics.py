from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.analytics import DashboardStats, RevenueChartPoint, JobStatusChartPoint, TopCustomer
from app.services.analytics_service import AnalyticsService
from app.api.v1.dependencies.auth import CurrentUser

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