import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class APIBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UUIDSchema(APIBase):
    id: uuid.UUID


class TimestampSchema(APIBase):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse[T](APIBase):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int