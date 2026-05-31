import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus


async def list_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: OrderStatus | None = None,
) -> list[Order]:
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.deleted_at.is_(None))
        .order_by(Order.created_at.desc())
    )
    if status is not None:
        query = query.where(Order.status == status)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_order_for_update(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.deleted_at.is_(None))
        .with_for_update()
    )
    return result.scalar_one_or_none()
