from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column

from app.models.base import Base
from app.models.user import enum_values


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    COD = "cod"


class PaymentEventStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="payments_amount_positive"),
        CheckConstraint(
            "amount_received IS NULL OR amount_received >= 0",
            name="payments_amount_received_non_negative",
        ),
        CheckConstraint(
            "change_amount IS NULL OR change_amount >= 0",
            name="payments_change_amount_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    method = Column(
        SQLEnum(
            PaymentMethod,
            name="payment_method",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    status = Column(
        SQLEnum(
            PaymentEventStatus,
            name="payment_event_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'pending'::payment_event_status"),
    )
    amount = Column(Numeric(12, 2), nullable=False)
    amount_received = Column(Numeric(12, 2))
    change_amount = Column(Numeric(12, 2))
    gateway_transaction_id = Column(String(255))
    bank_reference_number = Column(String(255))
    paid_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    order = relationship("Order", back_populates="payments")
    creator = relationship("User", back_populates="payments")
