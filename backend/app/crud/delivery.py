from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import DeliveryBatch, DeliveryOrder, BatchStatus
from app.schemas.delivery import DeliveryBatchCreate, DeliveryBatchUpdate, AssignOrdersToBatch


async def _generate_batch_number(db: AsyncSession) -> str:
    result = await db.execute(select(DeliveryBatch).order_by(DeliveryBatch.id.desc()).limit(1))
    last = result.scalar_one_or_none()
    next_id = (last.id + 1) if last else 1
    return f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{next_id:04d}"


async def get_batches(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[DeliveryBatch]:
    result = await db.execute(
        select(DeliveryBatch)
        .options(selectinload(DeliveryBatch.delivery_orders))
        .order_by(DeliveryBatch.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_batch(db: AsyncSession, batch_id: int) -> DeliveryBatch | None:
    result = await db.execute(
        select(DeliveryBatch)
        .options(selectinload(DeliveryBatch.delivery_orders))
        .where(DeliveryBatch.id == batch_id)
    )
    return result.scalar_one_or_none()


async def create_batch(db: AsyncSession, data: DeliveryBatchCreate) -> DeliveryBatch:
    batch_number = await _generate_batch_number(db)
    batch = DeliveryBatch(
        batch_number=batch_number,
        driver_name=data.driver_name,
        driver_phone=data.driver_phone,
        notes=data.notes,
        scheduled_at=data.scheduled_at,
    )
    db.add(batch)
    await db.flush()

    if data.order_ids:
        await _assign_orders(db, batch.id, data.order_ids)

    await db.commit()
    await db.refresh(batch)
    return batch


async def update_batch(db: AsyncSession, batch: DeliveryBatch, data: DeliveryBatchUpdate) -> DeliveryBatch:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(batch, field, value)

    if data.status == BatchStatus.dispatched and not batch.dispatched_at:
        batch.dispatched_at = datetime.now(timezone.utc)
    if data.status == BatchStatus.completed and not batch.completed_at:
        batch.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(batch)
    return batch


async def _assign_orders(db: AsyncSession, batch_id: int, order_ids: list[int]) -> None:
    result = await db.execute(
        select(DeliveryOrder).where(DeliveryOrder.order_id.in_(order_ids))
    )
    delivery_orders = result.scalars().all()
    for do in delivery_orders:
        do.batch_id = batch_id


async def assign_orders_to_batch(
    db: AsyncSession, batch: DeliveryBatch, data: AssignOrdersToBatch
) -> DeliveryBatch:
    await _assign_orders(db, batch.id, data.order_ids)
    await db.commit()
    await db.refresh(batch)
    return batch


async def get_unassigned_delivery_orders(db: AsyncSession) -> list[DeliveryOrder]:
    result = await db.execute(
        select(DeliveryOrder).where(DeliveryOrder.batch_id.is_(None))
    )
    return list(result.scalars().all())
