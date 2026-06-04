from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
