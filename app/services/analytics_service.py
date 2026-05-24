from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice, DayBookEntry, PaymentStatus
from app.models.job_card import JobCard, JobStatus
from app.models.inventory import InventoryItem
from app.models.customer import Customer
from app.schemas.analytics import (
    DashboardStats, RevenueStats, JobStats,
    InventoryStats, CustomerStats,
    RevenueChartPoint, JobStatusChartPoint, TopCustomer,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _start_of_month(d: date) -> date:
    return d.replace(day=1)


def _start_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_dashboard_stats(self) -> DashboardStats:
        today = _today()
        week_start = _start_of_week(today)
        month_start = _start_of_month(today)
        last_month_start = _start_of_month((month_start - timedelta(days=1)))
        last_month_end = month_start - timedelta(days=1)

        return DashboardStats(
            revenue=await self._revenue_stats(today, week_start, month_start, last_month_start, last_month_end),
            jobs=await self._job_stats(today, month_start),
            inventory=await self._inventory_stats(),
            customers=await self._customer_stats(month_start),
        )

    async def _revenue_stats(self, today, week_start, month_start, last_month_start, last_month_end) -> RevenueStats:
        async def paid_sum(start: date, end: date) -> Decimal:
            q = select(func.coalesce(func.sum(Invoice.paid_amount), 0)).where(
                Invoice.deleted_at.is_(None),
                func.date(Invoice.created_at) >= start,
                func.date(Invoice.created_at) <= end,
                Invoice.payment_status != PaymentStatus.CANCELLED,
            )
            result = await self.session.execute(q)
            return Decimal(str(result.scalar() or 0))

        this_month = await paid_sum(month_start, today)
        last_month = await paid_sum(last_month_start, last_month_end)

        if last_month > 0:
            growth = float(((this_month - last_month) / last_month) * 100)
        else:
            growth = 100.0 if this_month > 0 else 0.0

        return RevenueStats(
            today=await paid_sum(today, today),
            this_week=await paid_sum(week_start, today),
            this_month=this_month,
            last_month=last_month,
            growth_percent=round(growth, 1),
        )

    async def _job_stats(self, today: date, month_start: date) -> JobStats:
        async def count_status(status: JobStatus) -> int:
            q = select(func.count()).select_from(JobCard).where(
                JobCard.deleted_at.is_(None),
                JobCard.status == status,
            )
            return (await self.session.execute(q)).scalar_one()

        async def count_delivered(start: date, end: date) -> int:
            q = select(func.count()).select_from(JobCard).where(
                JobCard.deleted_at.is_(None),
                JobCard.status == JobStatus.DELIVERED,
                func.date(JobCard.updated_at) >= start,
                func.date(JobCard.updated_at) <= end,
            )
            return (await self.session.execute(q)).scalar_one()

        waiting       = await count_status(JobStatus.WAITING)
        diagnosing    = await count_status(JobStatus.DIAGNOSING)
        repairing     = await count_status(JobStatus.REPAIRING)
        waiting_parts = await count_status(JobStatus.WAITING_PARTS)
        ready         = await count_status(JobStatus.READY)

        return JobStats(
            total_active=waiting + diagnosing + repairing + waiting_parts + ready,
            waiting=waiting,
            diagnosing=diagnosing,
            repairing=repairing,
            waiting_parts=waiting_parts,
            ready=ready,
            completed_today=await count_delivered(today, today),
            completed_this_month=await count_delivered(month_start, today),
        )

    async def _inventory_stats(self) -> InventoryStats:
        total_q = select(func.count()).select_from(InventoryItem).where(InventoryItem.deleted_at.is_(None))
        total = (await self.session.execute(total_q)).scalar_one()

        low_q = select(func.count()).select_from(InventoryItem).where(
            InventoryItem.deleted_at.is_(None),
            InventoryItem.quantity <= InventoryItem.low_stock_threshold,
        )
        low = (await self.session.execute(low_q)).scalar_one()

        val_q = select(
            func.coalesce(func.sum(InventoryItem.quantity * InventoryItem.cost_price), 0)
        ).where(InventoryItem.deleted_at.is_(None))
        value = Decimal(str((await self.session.execute(val_q)).scalar() or 0))

        return InventoryStats(total_items=total, low_stock_count=low, total_value=value)

    async def _customer_stats(self, month_start: date) -> CustomerStats:
        total_q = select(func.count()).select_from(Customer).where(Customer.deleted_at.is_(None))
        total = (await self.session.execute(total_q)).scalar_one()

        new_q = select(func.count()).select_from(Customer).where(
            Customer.deleted_at.is_(None),
            func.date(Customer.created_at) >= month_start,
        )
        new = (await self.session.execute(new_q)).scalar_one()

        outstanding_q = select(func.count()).select_from(Customer).where(
            Customer.deleted_at.is_(None),
            Customer.outstanding_balance > 0,
        )
        outstanding = (await self.session.execute(outstanding_q)).scalar_one()

        return CustomerStats(total=total, new_this_month=new, with_outstanding=outstanding)

    async def get_revenue_chart(self, days: int = 30) -> list[RevenueChartPoint]:
        today = _today()
        points = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            d_str = str(d)

            income_q = select(func.coalesce(func.sum(Invoice.paid_amount), 0)).where(
                Invoice.deleted_at.is_(None),
                func.date(Invoice.created_at) == d,
                Invoice.payment_status != PaymentStatus.CANCELLED,
            )
            income = Decimal(str((await self.session.execute(income_q)).scalar() or 0))

            expense_q = select(func.coalesce(func.sum(DayBookEntry.amount), 0)).where(
                DayBookEntry.deleted_at.is_(None),
                DayBookEntry.entry_date == d_str,
                DayBookEntry.entry_type == "expense",
            )
            expense = Decimal(str((await self.session.execute(expense_q)).scalar() or 0))

            points.append(RevenueChartPoint(date=d_str, income=income, expense=expense))

        return points

    async def get_job_status_chart(self) -> list[JobStatusChartPoint]:
        colors = {
            "waiting":       "#f59e0b",
            "diagnosing":    "#3b82f6",
            "repairing":     "#8b5cf6",
            "waiting_parts": "#f97316",
            "ready":         "#10b981",
            "delivered":     "#6b7280",
        }
        points = []
        for status in JobStatus:
            if status == JobStatus.CANCELLED:
                continue
            q = select(func.count()).select_from(JobCard).where(
                JobCard.deleted_at.is_(None),
                JobCard.status == status,
            )
            count = (await self.session.execute(q)).scalar_one()
            points.append(JobStatusChartPoint(
                status=status.value.replace("_", " ").title(),
                count=count,
                color=colors.get(status.value, "#6b7280"),
            ))
        return points

    async def get_top_customers(self, limit: int = 5) -> list[TopCustomer]:
        q = (
            select(
                Invoice.customer_id,
                func.sum(Invoice.paid_amount).label("total_spent"),
                func.count(Invoice.id).label("job_count"),
            )
            .where(Invoice.deleted_at.is_(None))
            .group_by(Invoice.customer_id)
            .order_by(func.sum(Invoice.paid_amount).desc())
            .limit(limit)
        )
        rows = (await self.session.execute(q)).all()
        result = []
        for row in rows:
            customer = await self.session.get(Customer, row.customer_id)
            if customer:
                result.append(TopCustomer(
                    id=str(customer.id),
                    name=customer.name,
                    phone=customer.phone_primary,
                    total_spent=Decimal(str(row.total_spent or 0)),
                    job_count=row.job_count,
                ))
        return result