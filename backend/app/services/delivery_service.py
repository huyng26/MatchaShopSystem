"""
Delivery batching service.
Groups unassigned delivery orders into suggested batches.
A simple heuristic: batch by max orders per trip (configurable).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.delivery import get_unassigned_delivery_orders
from app.models.delivery import DeliveryOrder

MAX_ORDERS_PER_BATCH = 10


async def suggest_batches(db: AsyncSession, max_per_batch: int = MAX_ORDERS_PER_BATCH) -> list[list[int]]:
    """
    Returns a list of suggested groupings (each group = list of order IDs).
    Currently uses a simple FIFO chunking strategy.
    Future: integrate geographic clustering or time-window optimization.
    """
    unassigned: list[DeliveryOrder] = await get_unassigned_delivery_orders(db)
    order_ids = [do.order_id for do in unassigned]

    batches = []
    for i in range(0, len(order_ids), max_per_batch):
        batches.append(order_ids[i : i + max_per_batch])
    return batches
