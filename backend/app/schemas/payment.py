from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderPaymentStatus, OrderStatus
from app.models.payment import PaymentEventStatus, PaymentMethod


class PaymentCreate(BaseModel):
    order_id: UUID
    method: PaymentMethod
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    amount_received: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    gateway_transaction_id: str | None = Field(default=None, max_length=255)
    bank_reference_number: str | None = Field(default=None, max_length=255)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    method: PaymentMethod
    status: PaymentEventStatus
    amount: Decimal
    paid_at: datetime | None = None


class PaymentMethodRead(BaseModel):
    method: PaymentMethod


class StripeCheckoutSessionCreate(BaseModel):
    order_id: UUID
    ready_for_delivery: bool = False


class StripeCheckoutSessionRead(BaseModel):
    payment_id: UUID
    order_id: UUID
    stripe_checkout_session_id: str
    checkout_url: str
    qr_code_data_url: str
    expires_at: datetime | None = None
    status: PaymentEventStatus


class StripeCheckoutSessionStatusRead(BaseModel):
    payment_id: UUID
    order_id: UUID
    stripe_checkout_session_id: str
    payment_status: PaymentEventStatus
    order_status: OrderStatus
    order_payment_status: OrderPaymentStatus
    paid_at: datetime | None = None
    completed_at: datetime | None = None
