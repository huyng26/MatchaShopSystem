from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import (
    DeliveryTrip,
    DeliveryTripOrder,
    DeliveryTripOrderStatus,
    DeliveryTripStatus,
)
from app.models.finance import FinancialRecord, FinancialRecordType
from app.models.ingredients import Ingredient
from app.models.order import Order, OrderItem, OrderStatus, OrderType
from app.models.product import Product

ACTIVE_TRIP_STATUSES = (
    DeliveryTripStatus.PENDING_DISPATCH,
    DeliveryTripStatus.ASSIGNED,
    DeliveryTripStatus.IN_TRANSIT,
)


async def sum_revenue_by_created_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> Decimal:
    stmt = select(
        func.coalesce(func.sum(FinancialRecord.amount), Decimal("0")).label("total")
    ).where(
        FinancialRecord.record_type == FinancialRecordType.REVENUE,
        FinancialRecord.source_type == "order",
        FinancialRecord.created_at >= window_start,
        FinancialRecord.created_at < window_end,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def count_orders_by_created_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> int:
    stmt = select(func.count(Order.id)).where(
        Order.deleted_at.is_(None),
        Order.created_at >= window_start,
        Order.created_at < window_end,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def count_completed_orders_by_completed_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> int:
    stmt = select(func.count(Order.id)).where(
        Order.deleted_at.is_(None),
        Order.status == OrderStatus.COMPLETED,
        Order.completed_at >= window_start,
        Order.completed_at < window_end,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def count_delivery_queue_orders(db: AsyncSession) -> int:
    active_assignment = (
        select(DeliveryTripOrder.id)
        .join(DeliveryTrip, DeliveryTripOrder.trip_id == DeliveryTrip.id)
        .where(
            DeliveryTripOrder.order_id == Order.id,
            DeliveryTripOrder.status == DeliveryTripOrderStatus.ASSIGNED,
            DeliveryTrip.status.in_(ACTIVE_TRIP_STATUSES),
            DeliveryTrip.deleted_at.is_(None),
        )
    )
    stmt = select(func.count(Order.id)).where(
        Order.order_type == OrderType.DELIVERY,
        Order.status == OrderStatus.READY_FOR_DELIVERY,
        Order.deleted_at.is_(None),
        ~active_assignment.exists(),
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def count_low_stock_ingredients(db: AsyncSession) -> int:
    stmt = select(func.count(Ingredient.id)).where(
        Ingredient.deleted_at.is_(None),
        Ingredient.current_stock <= Ingredient.minimum_threshold,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def list_low_stock_ingredients(db: AsyncSession) -> Sequence[Ingredient]:
    stmt = (
        select(Ingredient)
        .where(
            Ingredient.deleted_at.is_(None),
            Ingredient.current_stock <= Ingredient.minimum_threshold,
        )
        .order_by(Ingredient.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def list_best_selling_products(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
    limit: int = 10,
) -> Sequence[tuple[Product, int, Decimal]]:
    quantity_sold = func.coalesce(func.sum(OrderItem.quantity), 0).label(
        "quantity_sold"
    )
    revenue = func.coalesce(func.sum(OrderItem.line_total), Decimal("0")).label(
        "revenue"
    )
    stmt = (
        select(Product, quantity_sold, revenue)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.deleted_at.is_(None),
            Order.status == OrderStatus.COMPLETED,
            Order.completed_at >= window_start,
            Order.completed_at < window_end,
        )
        .group_by(Product.id)
        .order_by(desc(quantity_sold), desc(revenue))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        (product, int(quantity), total)
        for product, quantity, total in result.all()
    ]


async def count_trips_by_created_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> int:
    stmt = select(func.count(DeliveryTrip.id)).where(
        DeliveryTrip.deleted_at.is_(None),
        DeliveryTrip.created_at >= window_start,
        DeliveryTrip.created_at < window_end,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def count_completed_trips_by_completed_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> int:
    stmt = select(func.count(DeliveryTrip.id)).where(
        DeliveryTrip.deleted_at.is_(None),
        DeliveryTrip.status.in_(
            (DeliveryTripStatus.COMPLETED, DeliveryTripStatus.RECONCILED)
        ),
        DeliveryTrip.completed_at >= window_start,
        DeliveryTrip.completed_at < window_end,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def get_average_delivery_minutes(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> Decimal:
    duration_minutes = func.extract(
        "epoch",
        DeliveryTrip.completed_at - DeliveryTrip.started_at,
    ) / 60
    stmt = select(
        func.coalesce(func.avg(duration_minutes), Decimal("0")).label("average")
    ).where(
        DeliveryTrip.deleted_at.is_(None),
        DeliveryTrip.started_at.is_not(None),
        DeliveryTrip.completed_at.is_not(None),
        DeliveryTrip.status.in_(
            (DeliveryTripStatus.COMPLETED, DeliveryTripStatus.RECONCILED)
        ),
        DeliveryTrip.completed_at >= window_start,
        DeliveryTrip.completed_at < window_end,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def sum_pending_cod_by_completed_window(
    db: AsyncSession,
    *,
    window_start: datetime,
    window_end: datetime,
) -> Decimal:
    stmt = select(
        func.coalesce(func.sum(DeliveryTrip.expected_cod_amount), Decimal("0")).label(
            "total"
        )
    ).where(
        DeliveryTrip.deleted_at.is_(None),
        DeliveryTrip.status == DeliveryTripStatus.COMPLETED,
        DeliveryTrip.completed_at >= window_start,
        DeliveryTrip.completed_at < window_end,
    )
    result = await db.execute(stmt)
    return result.scalar_one()
