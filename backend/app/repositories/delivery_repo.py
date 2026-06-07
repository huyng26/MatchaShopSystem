from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from secrets import token_hex
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery import (
    CodReconciliation,
    CodReconciliationStatus,
    DeliveryLocationLog,
    DeliveryTrip,
    DeliveryTripOrder,
    DeliveryTripOrderStatus,
    DeliveryTripStatus,
)
from app.models.order import Order, OrderStatus, OrderType

ACTIVE_TRIP_STATUSES = (
    DeliveryTripStatus.PENDING_DISPATCH,
    DeliveryTripStatus.ASSIGNED,
    DeliveryTripStatus.IN_TRANSIT,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def trip_code_exists(db: AsyncSession, trip_code: str) -> bool:
    stmt = select(exists().where(DeliveryTrip.trip_code == trip_code))
    result = await db.execute(stmt)
    return bool(result.scalar())


async def reserve_unique_trip_code(
    db: AsyncSession,
    *,
    prefix: str = "TRIP",
    max_attempts: int = 20,
) -> str:
    for _ in range(max_attempts):
        timestamp = utc_now().strftime("%Y%m%d%H%M%S")
        trip_code = f"{prefix}-{timestamp}-{token_hex(3).upper()}"
        if not await trip_code_exists(db, trip_code):
            return trip_code

    raise RuntimeError("unable_to_reserve_unique_trip_code")


async def list_delivery_queue_orders(db: AsyncSession) -> Sequence[Order]:
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
    stmt = (
        select(Order)
        .where(
            Order.order_type == OrderType.DELIVERY,
            Order.status == OrderStatus.READY_FOR_DELIVERY,
            Order.deleted_at.is_(None),
            ~active_assignment.exists(),
        )
        .options(selectinload(Order.payments))
        .order_by(Order.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_orders_by_ids_for_update(
    db: AsyncSession,
    order_ids: Iterable[UUID],
) -> Sequence[Order]:
    stmt = (
        select(Order)
        .where(
            Order.id.in_(list(order_ids)),
            Order.deleted_at.is_(None),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def order_has_active_assignment(db: AsyncSession, order_id: UUID) -> bool:
    active_assignment = (
        select(DeliveryTripOrder.id)
        .join(DeliveryTrip, DeliveryTripOrder.trip_id == DeliveryTrip.id)
        .where(
            DeliveryTripOrder.order_id == order_id,
            DeliveryTripOrder.status == DeliveryTripOrderStatus.ASSIGNED,
            DeliveryTrip.status.in_(ACTIVE_TRIP_STATUSES),
            DeliveryTrip.deleted_at.is_(None),
        )
    )
    result = await db.execute(select(active_assignment.exists()))
    return bool(result.scalar())


async def create_trip(
    db: AsyncSession,
    *,
    trip_code: str,
    expected_cod_amount: Decimal,
    total_distance_km: Decimal | None = None,
    total_duration_minutes: int | None = None,
    route_provider: str | None = None,
    created_by: UUID,
) -> DeliveryTrip:
    trip = DeliveryTrip(
        trip_code=trip_code,
        expected_cod_amount=expected_cod_amount,
        total_distance_km=total_distance_km,
        total_duration_minutes=total_duration_minutes,
        route_provider=route_provider,
        created_by=created_by,
    )
    db.add(trip)
    await db.flush()
    await db.refresh(trip)
    return trip


async def create_trip_orders(
    db: AsyncSession,
    *,
    trip_id: UUID,
    ordered_order_ids: list[UUID] | None = None,
    route_stops: Sequence[object] | None = None,
) -> Sequence[DeliveryTripOrder]:
    if route_stops is not None:
        rows = [
            DeliveryTripOrder(
                trip_id=trip_id,
                order_id=stop.order_id,
                stop_order=stop.stop_order,
                distance_from_previous_km=Decimal(
                    str(stop.distance_from_previous_km)
                ),
                duration_from_previous_minutes=stop.duration_from_previous_minutes,
            )
            for stop in route_stops
        ]
    else:
        rows = [
            DeliveryTripOrder(
                trip_id=trip_id,
                order_id=order_id,
                stop_order=index + 1,
            )
            for index, order_id in enumerate(ordered_order_ids or [])
        ]
    db.add_all(rows)
    await db.flush()
    for row in rows:
        await db.refresh(row)
    return rows


async def list_trips(
    db: AsyncSession,
    *,
    status: DeliveryTripStatus | None = None,
    shipper_id: UUID | None = None,
) -> Sequence[DeliveryTrip]:
    stmt = (
        select(DeliveryTrip)
        .where(DeliveryTrip.deleted_at.is_(None))
        .order_by(DeliveryTrip.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(DeliveryTrip.status == status)
    if shipper_id is not None:
        stmt = stmt.where(DeliveryTrip.shipper_id == shipper_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_trip_detail(db: AsyncSession, trip_id: UUID) -> DeliveryTrip | None:
    stmt = (
        select(DeliveryTrip)
        .where(
            DeliveryTrip.id == trip_id,
            DeliveryTrip.deleted_at.is_(None),
        )
        .options(
            selectinload(DeliveryTrip.trip_orders)
            .selectinload(DeliveryTripOrder.order)
            .selectinload(Order.payments),
            selectinload(DeliveryTrip.reconciliation),
        )
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is not None:
        trip.latest_location = await get_latest_location_log(db, trip.id)
    return trip


async def get_trip_for_update(
    db: AsyncSession,
    trip_id: UUID,
) -> DeliveryTrip | None:
    stmt = (
        select(DeliveryTrip)
        .where(
            DeliveryTrip.id == trip_id,
            DeliveryTrip.deleted_at.is_(None),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_trip_order_detail(
    db: AsyncSession,
    *,
    trip_id: UUID,
    order_id: UUID,
) -> DeliveryTripOrder | None:
    stmt = (
        select(DeliveryTripOrder)
        .where(
            DeliveryTripOrder.trip_id == trip_id,
            DeliveryTripOrder.order_id == order_id,
        )
        .options(
            selectinload(DeliveryTripOrder.order).selectinload(Order.payments),
            selectinload(DeliveryTripOrder.trip),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_trip_orders(
    db: AsyncSession,
    trip_id: UUID,
) -> Sequence[DeliveryTripOrder]:
    stmt = (
        select(DeliveryTripOrder)
        .where(DeliveryTripOrder.trip_id == trip_id)
        .options(selectinload(DeliveryTripOrder.order))
        .order_by(DeliveryTripOrder.stop_order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def shipper_has_active_trip(
    db: AsyncSession,
    shipper_id: UUID,
    *,
    exclude_trip_id: UUID | None = None,
) -> bool:
    active_trip = select(DeliveryTrip.id).where(
        DeliveryTrip.shipper_id == shipper_id,
        DeliveryTrip.status.in_(
            (DeliveryTripStatus.ASSIGNED, DeliveryTripStatus.IN_TRANSIT)
        ),
        DeliveryTrip.deleted_at.is_(None),
    )
    if exclude_trip_id is not None:
        active_trip = active_trip.where(DeliveryTrip.id != exclude_trip_id)

    result = await db.execute(select(active_trip.exists()))
    return bool(result.scalar())


async def create_location_log(
    db: AsyncSession,
    *,
    trip_id: UUID,
    shipper_id: UUID,
    latitude: Decimal,
    longitude: Decimal,
    recorded_at: datetime,
) -> DeliveryLocationLog:
    log = DeliveryLocationLog(
        trip_id=trip_id,
        shipper_id=shipper_id,
        latitude=latitude,
        longitude=longitude,
        recorded_at=recorded_at,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def get_latest_location_log(
    db: AsyncSession,
    trip_id: UUID,
) -> DeliveryLocationLog | None:
    stmt = (
        select(DeliveryLocationLog)
        .where(DeliveryLocationLog.trip_id == trip_id)
        .order_by(DeliveryLocationLog.recorded_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_reconciliation_by_trip(
    db: AsyncSession,
    trip_id: UUID,
) -> CodReconciliation | None:
    stmt = select(CodReconciliation).where(CodReconciliation.trip_id == trip_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_reconciliation(
    db: AsyncSession,
    *,
    trip_id: UUID,
    shipper_id: UUID,
    expected_amount: Decimal,
    actual_amount: Decimal,
    discrepancy_amount: Decimal,
    discrepancy_reason: str | None,
    status: CodReconciliationStatus,
    reconciled_by: UUID,
    reconciled_at: datetime,
) -> CodReconciliation:
    reconciliation = CodReconciliation(
        trip_id=trip_id,
        shipper_id=shipper_id,
        expected_amount=expected_amount,
        actual_amount=actual_amount,
        discrepancy_amount=discrepancy_amount,
        discrepancy_reason=discrepancy_reason,
        status=status,
        reconciled_by=reconciled_by,
        reconciled_at=reconciled_at,
    )
    db.add(reconciliation)
    await db.flush()
    await db.refresh(reconciliation)
    return reconciliation
