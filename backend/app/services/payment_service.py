from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.integration_contracts import write_audit
from app.models.order import (
    Order,
    OrderPaymentStatus,
    OrderStatus,
    OrderType,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.repositories import order as order_repo
from app.repositories import payment as payment_repo
from app.schemas.payment import BankTransferVerification, CardPaymentCreate, CashPaymentCreate
from app.services.errors import DomainError


@dataclass(frozen=True)
class CardAuthorization:
    approved: bool
    transaction_id: str


class MockCardPaymentGateway:
    async def authorize(self, approved: bool) -> CardAuthorization:
        return CardAuthorization(approved=approved, transaction_id=f"MOCK-{uuid.uuid4().hex.upper()}")


card_gateway = MockCardPaymentGateway()


async def _get_payable_order(db: AsyncSession, order_id: uuid.UUID) -> Order:
    order = await order_repo.get_order_for_update(db, order_id)
    if order is None:
        raise DomainError("Order not found", 404)
    if order.status in {OrderStatus.completed, OrderStatus.cancelled}:
        raise DomainError("Completed or cancelled orders cannot receive payments")
    if await payment_repo.has_successful_payment(db, order.id):
        raise DomainError("Order already has a successful payment")
    return order


async def list_order_payments(db: AsyncSession, order_id: uuid.UUID) -> list[Payment]:
    if await order_repo.get_order(db, order_id) is None:
        raise DomainError("Order not found", 404)
    return await payment_repo.list_order_payments(db, order_id)


async def get_payment(db: AsyncSession, payment_id: uuid.UUID) -> Payment:
    payment = await payment_repo.get_payment(db, payment_id)
    if payment is None:
        raise DomainError("Payment not found", 404)
    return payment


async def record_cash_payment(
    db: AsyncSession, order_id: uuid.UUID, data: CashPaymentCreate, actor_user_id: uuid.UUID
) -> Payment:
    async with db.begin():
        order = await _get_payable_order(db, order_id)
        total = Decimal(order.total_amount)
        if data.amount_received < total:
            raise DomainError("Cash received is less than the order total")
        payment = Payment(
            order_id=order.id,
            method=PaymentMethod.cash,
            status=PaymentStatus.success,
            amount=total,
            amount_received=data.amount_received,
            change_amount=data.amount_received - total,
            paid_at=datetime.now(timezone.utc),
            created_by=actor_user_id,
        )
        db.add(payment)
        order.payment_status = OrderPaymentStatus.paid
        await db.flush()
        await write_audit(db, actor_user_id, "payment.success", "payment", payment.id)
    return payment


async def record_card_payment(
    db: AsyncSession, order_id: uuid.UUID, data: CardPaymentCreate, actor_user_id: uuid.UUID
) -> Payment:
    async with db.begin():
        order = await _get_payable_order(db, order_id)
        authorization = await card_gateway.authorize(data.simulate_approved)
        payment = Payment(
            order_id=order.id,
            method=PaymentMethod.card,
            status=PaymentStatus.success if authorization.approved else PaymentStatus.failed,
            amount=order.total_amount,
            gateway_transaction_id=authorization.transaction_id,
            paid_at=datetime.now(timezone.utc) if authorization.approved else None,
            created_by=actor_user_id,
        )
        db.add(payment)
        if authorization.approved:
            order.payment_status = OrderPaymentStatus.paid
        await db.flush()
        action = "payment.success" if authorization.approved else "payment.failed"
        await write_audit(db, actor_user_id, action, "payment", payment.id)
    return payment


async def create_bank_transfer(
    db: AsyncSession, order_id: uuid.UUID, actor_user_id: uuid.UUID
) -> Payment:
    async with db.begin():
        order = await _get_payable_order(db, order_id)
        payment = Payment(
            order_id=order.id,
            method=PaymentMethod.bank_transfer,
            status=PaymentStatus.pending,
            amount=order.total_amount,
            bank_reference_number=f"BANK-{order.order_code}",
            created_by=actor_user_id,
        )
        db.add(payment)
    return payment


async def verify_bank_transfer(
    db: AsyncSession,
    payment_id: uuid.UUID,
    data: BankTransferVerification,
    actor_user_id: uuid.UUID,
) -> Payment:
    async with db.begin():
        payment = await payment_repo.get_payment_for_update(db, payment_id)
        if payment is None:
            raise DomainError("Payment not found", 404)
        if payment.method != PaymentMethod.bank_transfer or payment.status != PaymentStatus.pending:
            raise DomainError("Payment is not a pending bank transfer")
        order = await _get_payable_order(db, payment.order_id)
        if data.amount_received != Decimal(order.total_amount):
            raise DomainError("Transferred amount does not match the order total")
        payment.amount_received = data.amount_received
        payment.bank_reference_number = data.bank_reference_number
        payment.status = PaymentStatus.success
        payment.paid_at = datetime.now(timezone.utc)
        order.payment_status = OrderPaymentStatus.paid
        await write_audit(db, actor_user_id, "payment.success", "payment", payment.id)
    return payment


async def create_cod_payment(
    db: AsyncSession, order_id: uuid.UUID, actor_user_id: uuid.UUID
) -> Payment:
    async with db.begin():
        order = await _get_payable_order(db, order_id)
        if order.order_type != OrderType.delivery:
            raise DomainError("COD is only available for delivery orders")
        payment = Payment(
            order_id=order.id,
            method=PaymentMethod.cod,
            status=PaymentStatus.pending,
            amount=order.total_amount,
            created_by=actor_user_id,
        )
        db.add(payment)
    return payment
