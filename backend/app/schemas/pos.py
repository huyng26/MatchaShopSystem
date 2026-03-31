from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.order import OrderType, OrderStatus, PaymentMethod


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderCreate(BaseModel):
    order_type: OrderType
    customer_id: int | None = None
    notes: str | None = None
    items: list[OrderItemCreate]
    # Required when order_type == delivery
    delivery_address: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class PaymentCreate(BaseModel):
    method: PaymentMethod
    amount: Decimal
    reference: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    method: PaymentMethod
    amount: Decimal
    reference: str | None
    paid_at: datetime


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_type: OrderType
    status: OrderStatus
    customer_id: int | None
    notes: str | None
    total_amount: Decimal
    items: list[OrderItemResponse] = []
    payment: PaymentResponse | None = None
    created_at: datetime
    updated_at: datetime
