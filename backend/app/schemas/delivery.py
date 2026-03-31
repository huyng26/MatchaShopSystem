from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.delivery import BatchStatus, DeliveryStatus


class DeliveryOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    batch_id: int | None
    delivery_address: str
    status: DeliveryStatus
    delivery_notes: str | None
    delivered_at: datetime | None


class DeliveryBatchCreate(BaseModel):
    driver_name: str | None = None
    driver_phone: str | None = None
    notes: str | None = None
    scheduled_at: datetime | None = None
    order_ids: list[int] = []  # delivery order IDs to add to this batch


class DeliveryBatchUpdate(BaseModel):
    driver_name: str | None = None
    driver_phone: str | None = None
    status: BatchStatus | None = None
    notes: str | None = None
    scheduled_at: datetime | None = None


class DeliveryBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_number: str
    driver_name: str | None
    driver_phone: str | None
    status: BatchStatus
    notes: str | None
    scheduled_at: datetime | None
    dispatched_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    delivery_orders: list[DeliveryOrderResponse] = []


class AssignOrdersToBatch(BaseModel):
    order_ids: list[int]
