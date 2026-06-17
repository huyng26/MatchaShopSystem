from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import ok, raise_service_error, read_list, read_one
from app.core.constants import UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.user import User
from app.schemas.shipper import (
    ShipperLocationLogRead,
    ShipperLocationUpdate,
    ShipperOrderDelivered,
    ShipperOrderFailed,
    ShipperPerformanceRead,
    ShipperTripDetailRead,
    ShipperTripRead,
)
from app.services import shipper_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("/trips")
async def list_shipper_trips(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    trips = await shipper_service.list_assigned_trips(
        db,
        current_user=current_user,
    )
    return ok(read_list(ShipperTripRead, trips))


@router.get("/trips/{trip_id}")
async def get_shipper_trip(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        trip = await shipper_service.get_assigned_trip(
            db,
            trip_id,
            current_user=current_user,
        )
        return ok(read_one(ShipperTripDetailRead, trip))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/performance")
async def get_shipper_performance(
    month: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        performance = await shipper_service.get_performance(
            db,
            current_user=current_user,
            month=month,
        )
        return ok(ShipperPerformanceRead.model_validate(performance))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/start")
async def start_shipper_trip(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        trip = await shipper_service.start_assigned_trip(
            db,
            trip_id,
            current_user=current_user,
        )
        return ok(
            read_one(ShipperTripDetailRead, trip),
            message="Delivery trip started successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/location")
async def update_shipper_location(
    trip_id: UUID,
    payload: ShipperLocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        location = await shipper_service.update_location(
            db,
            trip_id,
            payload,
            current_user=current_user,
        )
        return ok(
            read_one(ShipperLocationLogRead, location),
            message="Delivery location updated successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/orders/{order_id}/delivered")
async def mark_shipper_order_delivered(
    trip_id: UUID,
    order_id: UUID,
    payload: ShipperOrderDelivered,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        trip = await shipper_service.mark_order_delivered(
            db,
            trip_id,
            order_id,
            payload,
            current_user=current_user,
        )
        return ok(
            read_one(ShipperTripDetailRead, trip),
            message="Delivery order marked delivered successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/orders/{order_id}/failed")
async def mark_shipper_order_failed(
    trip_id: UUID,
    order_id: UUID,
    payload: ShipperOrderFailed,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SHIPPER)),
) -> dict[str, Any]:
    try:
        trip = await shipper_service.mark_order_failed(
            db,
            trip_id,
            order_id,
            payload,
            current_user=current_user,
        )
        return ok(
            read_one(ShipperTripDetailRead, trip),
            message="Delivery order marked failed successfully",
        )
    except ServiceError as error:
        raise_service_error(error)
