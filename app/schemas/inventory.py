import uuid
from datetime import datetime
from decimal import Decimal
from app.schemas.base import APIBase


class SupplierCreate(APIBase):
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    pan_vat: str | None = None
    notes: str | None = None


class SupplierUpdate(APIBase):
    name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    pan_vat: str | None = None
    notes: str | None = None


class SupplierResponse(APIBase):
    id: uuid.UUID
    name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    address: str | None
    pan_vat: str | None
    notes: str | None
    created_at: datetime
    parts_count: int = 0


class InventoryItemCreate(APIBase):
    name: str
    part_number: str | None = None
    category: str
    description: str | None = None
    unit: str = "piece"
    quantity: int = 0
    low_stock_threshold: int = 5
    cost_price: Decimal
    selling_price: Decimal
    supplier_id: uuid.UUID | None = None
    barcode: str | None = None
    location: str | None = None


class InventoryItemUpdate(APIBase):
    name: str | None = None
    part_number: str | None = None
    category: str | None = None
    description: str | None = None
    unit: str | None = None
    low_stock_threshold: int | None = None
    cost_price: Decimal | None = None
    selling_price: Decimal | None = None
    supplier_id: uuid.UUID | None = None
    barcode: str | None = None
    location: str | None = None


class InventoryItemResponse(APIBase):
    id: uuid.UUID
    name: str
    part_number: str | None
    category: str
    description: str | None
    unit: str
    quantity: int
    low_stock_threshold: int
    cost_price: Decimal
    selling_price: Decimal
    supplier_id: uuid.UUID | None
    barcode: str | None
    location: str | None
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime
    supplier_name: str | None = None
    supplier_phone: str | None = None


class StockAdjustment(APIBase):
    quantity_change: int
    reason: str
    reference: str | None = None


class InventoryListItem(APIBase):
    id: uuid.UUID
    name: str
    part_number: str | None
    category: str
    unit: str
    quantity: int
    low_stock_threshold: int
    selling_price: Decimal
    cost_price: Decimal
    is_low_stock: bool = False
    supplier_id: uuid.UUID | None = None
    supplier_name: str | None = None