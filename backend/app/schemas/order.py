from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.order import OrderPaymentStatus, OrderStatus, OrderType


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderCreate(BaseModel):
    order_type: OrderType
    customer_id: uuid.UUID | None = None
    customer_name: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = None
    delivery_latitude: Decimal | None = None
    delivery_longitude: Decimal | None = None
    note: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_delivery_and_items(self) -> "OrderCreate":
        if self.order_type == OrderType.delivery and not self.delivery_address:
            raise ValueError("delivery_address is required for delivery orders")
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Order items must contain unique products")
        return self


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_code: str
    customer_id: uuid.UUID | None
    order_type: OrderType
    status: OrderStatus
    payment_status: OrderPaymentStatus
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    customer_name: str | None
    customer_phone: str | None
    delivery_address: str | None
    delivery_latitude: Decimal | None
    delivery_longitude: Decimal | None
    note: str | None
    items: list[OrderItemResponse] = Field(default_factory=list)
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    cancelled_at: datetime | None
