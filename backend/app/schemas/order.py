from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentMethod
from app.schemas.common import validate_non_empty
from app.schemas.customer import normalize_phone


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    @model_validator(mode="before")
    @classmethod
    def populate_product_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        product = getattr(data, "product", None)
        return {
            "product_id": getattr(data, "product_id", None),
            "product_name": getattr(product, "name", None),
            "quantity": getattr(data, "quantity", None),
            "unit_price": getattr(data, "unit_price", None),
            "line_total": getattr(data, "line_total", None),
        }


class OrderCreate(BaseModel):
    customer_id: UUID | None = None
    order_type: OrderType
    create_customer_profile: bool = False
    discount_amount: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )
    customer_name: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)
    delivery_address: str | None = None
    delivery_latitude: Decimal | None = Field(
        default=None, ge=-90, le=90, max_digits=10, decimal_places=7
    )
    delivery_longitude: Decimal | None = Field(
        default=None, ge=-180, le=180, max_digits=10, decimal_places=7
    )
    note: str | None = None
    items: list[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value: str | None) -> str | None:
        return validate_non_empty(value) if value is not None else value

    @field_validator("customer_phone")
    @classmethod
    def validate_customer_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_code: str
    customer_id: UUID | None = None
    order_type: OrderType
    status: OrderStatus
    payment_status: OrderPaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    customer_name: str | None = None
    customer_phone: str | None = None
    delivery_address: str | None = None
    delivery_latitude: Decimal | None = None
    delivery_longitude: Decimal | None = None
    delivery_formatted_address: str | None = None
    delivery_place_id: str | None = None
    geocoded_at: datetime | None = None
    geocoding_status: str | None = None
    map_provider: str | None = None
    note: str | None = None
    created_at: datetime
    items: list[OrderItemRead]


class OrderDetailRead(OrderRead):
    updated_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class OrderListFilters(BaseModel):
    status: OrderStatus | None = None
    payment_status: OrderPaymentStatus | None = None
    order_type: OrderType | None = None
    customer_id: UUID | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


class OrderReadyForDelivery(BaseModel):
    payment_method: PaymentMethod | None = None


class OrderCancelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    cancelled_at: datetime | None = None


class OrderCompleteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    inventory_deducted: bool
    financial_records_created: bool
    completed_at: datetime | None = None
