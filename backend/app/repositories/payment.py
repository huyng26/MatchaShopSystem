import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Payment, PaymentStatus


async def get_payment(db: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_payment_for_update(db: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.id == payment_id).with_for_update())
    return result.scalar_one_or_none()


async def list_order_payments(db: AsyncSession, order_id: uuid.UUID) -> list[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
    )
    return list(result.scalars().all())


async def has_successful_payment(db: AsyncSession, order_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Payment.id).where(
            Payment.order_id == order_id, Payment.status == PaymentStatus.success
        )
    )
    return result.first() is not None
