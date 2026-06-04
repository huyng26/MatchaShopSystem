from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentEventStatus, PaymentMethod


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_payments(
    db: AsyncSession,
    *,
    order_id: UUID | None = None,
    method: PaymentMethod | None = None,
    status: PaymentEventStatus | None = None,
) -> Sequence[Payment]:
    stmt = select(Payment).order_by(Payment.created_at.desc())
    if order_id is not None:
        stmt = stmt.where(Payment.order_id == order_id)
    if method is not None:
        stmt = stmt.where(Payment.method == method)
    if status is not None:
        stmt = stmt.where(Payment.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_payment_event(
    db: AsyncSession,
    *,
    order_id: UUID,
    method: PaymentMethod,
    status: PaymentEventStatus,
    amount: Decimal,
    created_by: UUID,
    amount_received: Decimal | None = None,
    change_amount: Decimal | None = None,
    gateway_transaction_id: str | None = None,
    bank_reference_number: str | None = None,
    paid_at: datetime | None = None,
) -> Payment:
    payment = Payment(
        order_id=order_id,
        method=method,
        status=status,
        amount=amount,
        amount_received=amount_received,
        change_amount=change_amount,
        gateway_transaction_id=gateway_transaction_id,
        bank_reference_number=bank_reference_number,
        paid_at=paid_at,
        created_by=created_by,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def get_successful_payment_for_order(
    db: AsyncSession,
    order_id: UUID,
) -> Payment | None:
    stmt = (
        select(Payment)
        .where(
            Payment.order_id == order_id,
            Payment.status == PaymentEventStatus.SUCCESS,
        )
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_pending_cod_payment_for_order(
    db: AsyncSession,
    order_id: UUID,
) -> Payment | None:
    stmt = (
        select(Payment)
        .where(
            Payment.order_id == order_id,
            Payment.method == PaymentMethod.COD,
            Payment.status == PaymentEventStatus.PENDING,
        )
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def mark_payment_success(
    db: AsyncSession,
    payment: Payment,
    *,
    amount_received: Decimal,
    paid_at: datetime,
) -> Payment:
    payment.status = PaymentEventStatus.SUCCESS
    payment.amount_received = amount_received
    payment.change_amount = Decimal("0.00")
    payment.paid_at = paid_at
    payment.updated_at = utc_now()
    await db.flush()
    await db.refresh(payment)
    return payment


async def sum_successful_payments_for_order(
    db: AsyncSession,
    order_id: UUID,
) -> Decimal:
    stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.order_id == order_id,
        Payment.status == PaymentEventStatus.SUCCESS,
    )
    result = await db.execute(stmt)
    return Decimal(result.scalar_one())
