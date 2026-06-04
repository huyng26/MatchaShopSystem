from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import (
    created,
    ok,
    raise_service_error,
    read_list,
    read_one,
)
from app.core.constants import UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.delivery import DeliveryTripStatus
from app.models.user import User
from app.schemas.common import to_jsonable
from app.schemas.delivery import (
    CodReconciliationRead,
    DeliveryBatchSuggestRequest,
    DeliveryCodReconcile,
    DeliveryQueueItem,
    DeliveryTripAssign,
    DeliveryTripCreate,
    DeliveryTripDetailRead,
    DeliveryTripRead,
)
from app.services import delivery_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("/queue")
async def get_delivery_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    queue = await delivery_service.list_delivery_queue(db)
    return ok(to_jsonable([DeliveryQueueItem.model_validate(item) for item in queue]))


@router.post("/batch/suggest")
async def suggest_delivery_batches(
    payload: DeliveryBatchSuggestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    try:
        batches = await delivery_service.suggest_batches(db, payload)
        return ok(to_jsonable(batches))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips")
async def create_delivery_trip(
    payload: DeliveryTripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    try:
        trip = await delivery_service.create_trip(
            db,
            payload,
            current_user=current_user,
        )
        return created(
            read_one(DeliveryTripDetailRead, trip),
            message="Delivery trip created successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.get("/trips")
async def list_delivery_trips(
    status: DeliveryTripStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    trips = await delivery_service.list_trips(
        db,
        current_user=current_user,
        status=status,
    )
    return ok(read_list(DeliveryTripRead, trips))


@router.get("/trips/{trip_id}")
async def get_delivery_trip(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    try:
        trip = await delivery_service.get_trip(
            db,
            trip_id,
            current_user=current_user,
        )
        return ok(read_one(DeliveryTripDetailRead, trip))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/assign")
async def assign_delivery_trip(
    trip_id: UUID,
    payload: DeliveryTripAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    try:
        trip = await delivery_service.assign_shipper(
            db,
            trip_id,
            payload.shipper_id,
        )
        return ok(
            read_one(DeliveryTripDetailRead, trip),
            message="Delivery trip assigned successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.post("/trips/{trip_id}/reconcile")
async def reconcile_delivery_cod(
    trip_id: UUID,
    payload: DeliveryCodReconcile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    ),
) -> dict[str, Any]:
    try:
        reconciliation = await delivery_service.reconcile_cod(
            db,
            trip_id,
            payload,
            current_user=current_user,
        )
        return created(
            read_one(CodReconciliationRead, reconciliation),
            message="COD reconciled successfully",
        )
    except ServiceError as error:
        raise_service_error(error)
