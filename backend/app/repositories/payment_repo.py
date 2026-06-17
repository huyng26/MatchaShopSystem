from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
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
    metadata: dict | None = None,
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
        metadata_=metadata or {},
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


async def get_payment_by_gateway_transaction_id(
    db: AsyncSession,
    gateway_transaction_id: str,
    *,
    for_update: bool = False,
    load_order: bool = False,
) -> Payment | None:
    stmt = select(Payment).where(
        Payment.gateway_transaction_id == gateway_transaction_id
    )
    if load_order:
        stmt = stmt.options(
            selectinload(Payment.order).selectinload(Order.payments),
            selectinload(Payment.order).selectinload(Order.items),
        )
    if for_update:
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_latest_pending_stripe_checkout_payment_for_order(
    db: AsyncSession,
    order_id: UUID,
) -> Payment | None:
    stmt = (
        select(Payment)
        .where(
            Payment.order_id == order_id,
            Payment.method == PaymentMethod.BANK_TRANSFER,
            Payment.status == PaymentEventStatus.PENDING,
            Payment.gateway_transaction_id.is_not(None),
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
    bank_reference_number: str | None = None,
    metadata: dict | None = None,
) -> Payment:
    payment.status = PaymentEventStatus.SUCCESS
    payment.amount_received = amount_received
    payment.change_amount = Decimal("0.00")
    if bank_reference_number is not None:
        payment.bank_reference_number = bank_reference_number
    if metadata is not None:
        payment.metadata_ = metadata
    payment.paid_at = paid_at
    payment.updated_at = utc_now()
    await db.flush()
    await db.refresh(payment)
    return payment


async def update_payment_status(
    db: AsyncSession,
    payment: Payment,
    *,
    status: PaymentEventStatus,
    metadata: dict | None = None,
) -> Payment:
    payment.status = status
    if metadata is not None:
        payment.metadata_ = metadata
    payment.updated_at = utc_now()
    await db.flush()
    await db.refresh(payment)
    return payment


async def update_pending_cod_amount(
    db: AsyncSession,
    payment: Payment,
    *,
    amount: Decimal,
) -> Payment:
    payment.amount = amount
    payment.amount_received = None
    payment.change_amount = None
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
