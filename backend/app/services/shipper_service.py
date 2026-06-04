from collections.abc import Sequence
from datetime import timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import DeliveryLocationLog, DeliveryTrip, DeliveryTripStatus
from app.models.user import User
from app.schemas.shipper import (
    ShipperLocationUpdate,
    ShipperOrderDelivered,
    ShipperOrderFailed,
)
from app.services import delivery_service

ACTIVE_TRIP_STATUSES = {
    DeliveryTripStatus.ASSIGNED,
    DeliveryTripStatus.IN_TRANSIT,
}
ACTIVE_TRIP_STATUS_VALUES = {status.value for status in ACTIVE_TRIP_STATUSES}


async def list_assigned_trips(
    db: AsyncSession,
    *,
    current_user: User,
) -> Sequence[DeliveryTrip]:
    trips = await delivery_service.list_trips(db, current_user=current_user)
    return sorted(
        trips,
        key=lambda trip: (
            getattr(trip.status, "value", trip.status)
            not in ACTIVE_TRIP_STATUS_VALUES,
            -_created_at_timestamp(trip),
        ),
        reverse=False,
    )


async def get_assigned_trip(
    db: AsyncSession,
    trip_id: UUID,
    *,
    current_user: User,
) -> DeliveryTrip:
    return await delivery_service.get_trip(db, trip_id, current_user=current_user)


async def start_assigned_trip(
    db: AsyncSession,
    trip_id: UUID,
    *,
    current_user: User,
) -> DeliveryTrip:
    return await delivery_service.start_trip(db, trip_id, current_user=current_user)


async def update_location(
    db: AsyncSession,
    trip_id: UUID,
    payload: ShipperLocationUpdate,
    *,
    current_user: User,
) -> DeliveryLocationLog:
    return await delivery_service.update_location(
        db,
        trip_id,
        payload,
        current_user=current_user,
    )


async def mark_order_delivered(
    db: AsyncSession,
    trip_id: UUID,
    order_id: UUID,
    payload: ShipperOrderDelivered,
    *,
    current_user: User,
) -> DeliveryTrip:
    return await delivery_service.mark_order_delivered(
        db,
        trip_id,
        order_id,
        payload,
        current_user=current_user,
    )


async def mark_order_failed(
    db: AsyncSession,
    trip_id: UUID,
    order_id: UUID,
    payload: ShipperOrderFailed,
    *,
    current_user: User,
) -> DeliveryTrip:
    return await delivery_service.mark_order_failed(
        db,
        trip_id,
        order_id,
        payload,
        current_user=current_user,
    )


def _created_at_timestamp(trip: DeliveryTrip) -> float:
    created_at = getattr(trip, "created_at", None)
    if created_at is None:
        return 0.0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return created_at.timestamp()
