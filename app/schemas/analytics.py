from decimal import Decimal
from app.schemas.base import APIBase


class RevenueStats(APIBase):
    today: Decimal
    this_week: Decimal
    this_month: Decimal
    last_month: Decimal
    growth_percent: float


class JobStats(APIBase):
    total_active: int
    waiting: int
    diagnosing: int
    repairing: int
    waiting_parts: int
    ready: int
    completed_today: int
    completed_this_month: int


class InventoryStats(APIBase):
    total_items: int
    low_stock_count: int
    total_value: Decimal


class CustomerStats(APIBase):
    total: int
    new_this_month: int
    with_outstanding: int


class DashboardStats(APIBase):
    revenue: RevenueStats
    jobs: JobStats
    inventory: InventoryStats
    customers: CustomerStats


class RevenueChartPoint(APIBase):
    date: str
    income: Decimal
    expense: Decimal


class JobStatusChartPoint(APIBase):
    status: str
    count: int
    color: str


class TopCustomer(APIBase):
    id: str
    name: str
    phone: str
    total_spent: Decimal
    job_count: int