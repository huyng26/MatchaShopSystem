from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.delivery import (
    CodReconciliationStatus,
    DeliveryTripOrderStatus,
    DeliveryTripStatus,
)
from app.models.order import OrderPaymentStatus
from app.models.payment import PaymentEventStatus, PaymentMethod


class DeliveryQueueItem(BaseModel):
    order_id: UUID
    order_code: str
    customer_name: str | None = None
    customer_phone: str | None = None
    delivery_address: str | None = None
    delivery_latitude: Decimal | None = None
    delivery_longitude: Decimal | None = None
    total_amount: Decimal
    payment_status: OrderPaymentStatus
    payment_method: PaymentMethod | None = None
    amount_to_collect: Decimal
    waiting_time: str
    created_at: datetime


class DeliveryBatchSuggestRequest(BaseModel):
    order_ids: list[UUID] | None = Field(default=None, min_length=1)
    max_orders_per_trip: int = Field(default=4, ge=1, le=20)


class DeliverySuggestedStop(BaseModel):
    order_id: UUID
    order_code: str
    stop_order: int
    distance_from_previous_km: float


class DeliverySuggestedBatch(BaseModel):
    orders: list[DeliverySuggestedStop]
    total_distance_km: float
    expected_cod_amount: Decimal


class DeliveryTripCreate(BaseModel):
    order_ids: list[UUID] = Field(..., min_length=1)
    use_auto_route: bool = True


class DeliveryTripAssign(BaseModel):
    shipper_id: UUID


class DeliveryLocationUpdate(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90, max_digits=10, decimal_places=7)
    longitude: Decimal = Field(..., ge=-180, le=180, max_digits=10, decimal_places=7)


class DeliveryOrderDelivered(BaseModel):
    cod_collected: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    note: str | None = Field(default=None, max_length=1000)


class DeliveryOrderFailed(BaseModel):
    failed_reason: str = Field(..., min_length=1, max_length=500)
    note: str | None = Field(default=None, max_length=1000)


class DeliveryCodReconcile(BaseModel):
    actual_amount: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)
    discrepancy_reason: str | None = Field(default=None, max_length=1000)


class DeliveryTripOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    order_code: str
    stop_order: int
    status: DeliveryTripOrderStatus
    cod_collected: Decimal
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failed_reason: str | None = None
    note: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    delivery_address: str | None = None
    delivery_latitude: Decimal | None = None
    delivery_longitude: Decimal | None = None
    total_amount: Decimal
    payment_status: OrderPaymentStatus
    payment_method: PaymentMethod | None = None
    amount_to_collect: Decimal

    @model_validator(mode="before")
    @classmethod
    def populate_order_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        order = getattr(data, "order", None)
        return {
            "id": getattr(data, "id", None),
            "order_id": getattr(data, "order_id", None),
            "order_code": getattr(order, "order_code", None),
            "stop_order": getattr(data, "stop_order", None),
            "status": getattr(data, "status", None),
            "cod_collected": getattr(data, "cod_collected", None),
            "delivered_at": getattr(data, "delivered_at", None),
            "failed_at": getattr(data, "failed_at", None),
            "failed_reason": getattr(data, "failed_reason", None),
            "note": getattr(data, "note", None),
            "customer_name": getattr(order, "customer_name", None),
            "customer_phone": getattr(order, "customer_phone", None),
            "delivery_address": getattr(order, "delivery_address", None),
            "delivery_latitude": getattr(order, "delivery_latitude", None),
            "delivery_longitude": getattr(order, "delivery_longitude", None),
            "total_amount": getattr(order, "total_amount", None),
            "payment_status": getattr(order, "payment_status", None),
            "payment_method": payment_method_for_order(order),
            "amount_to_collect": amount_to_collect_for_order(order),
        }


class DeliveryTripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_code: str
    shipper_id: UUID | None = None
    status: DeliveryTripStatus
    expected_cod_amount: Decimal
    actual_cod_amount: Decimal | None = None
    discrepancy_amount: Decimal | None = None
    discrepancy_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reconciled_at: datetime | None = None
    created_at: datetime


class DeliveryTripDetailRead(DeliveryTripRead):
    orders: list[DeliveryTripOrderRead]

    @model_validator(mode="before")
    @classmethod
    def populate_trip_orders(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        return {
            "id": getattr(data, "id", None),
            "trip_code": getattr(data, "trip_code", None),
            "shipper_id": getattr(data, "shipper_id", None),
            "status": getattr(data, "status", None),
            "expected_cod_amount": getattr(data, "expected_cod_amount", None),
            "actual_cod_amount": getattr(data, "actual_cod_amount", None),
            "discrepancy_amount": getattr(data, "discrepancy_amount", None),
            "discrepancy_reason": getattr(data, "discrepancy_reason", None),
            "started_at": getattr(data, "started_at", None),
            "completed_at": getattr(data, "completed_at", None),
            "reconciled_at": getattr(data, "reconciled_at", None),
            "created_at": getattr(data, "created_at", None),
            "orders": getattr(data, "trip_orders", []),
        }


class DeliveryLocationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    shipper_id: UUID
    latitude: Decimal
    longitude: Decimal
    recorded_at: datetime


class CodReconciliationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    shipper_id: UUID
    expected_amount: Decimal
    actual_amount: Decimal
    discrepancy_amount: Decimal
    discrepancy_reason: str | None = None
    status: CodReconciliationStatus
    reconciled_by: UUID
    reconciled_at: datetime


def payment_method_for_order(order: Any) -> PaymentMethod | None:
    if order is None:
        return None
    if getattr(order, "payment_status", None) == OrderPaymentStatus.UNPAID:
        return PaymentMethod.COD

    for payment in getattr(order, "payments", []) or []:
        if getattr(payment, "status", None) == PaymentEventStatus.SUCCESS:
            return getattr(payment, "method", None)
    return None


def amount_to_collect_for_order(order: Any) -> Decimal:
    if order is None:
        return Decimal("0.00")
    if getattr(order, "payment_status", None) == OrderPaymentStatus.UNPAID:
        return getattr(order, "total_amount", Decimal("0.00"))
    return Decimal("0.00")
