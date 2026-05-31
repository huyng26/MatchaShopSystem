from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import PaymentMethod, PaymentStatus


class CashPaymentCreate(BaseModel):
    amount_received: Decimal = Field(gt=0)


class CardPaymentCreate(BaseModel):
    simulate_approved: bool = True


class BankTransferVerification(BaseModel):
    amount_received: Decimal = Field(gt=0)
    bank_reference_number: str = Field(min_length=1, max_length=255)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    amount_received: Decimal | None
    change_amount: Decimal | None
    gateway_transaction_id: str | None
    bank_reference_number: str | None
    paid_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
