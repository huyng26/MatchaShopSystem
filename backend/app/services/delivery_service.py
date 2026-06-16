from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, UserRole
from app.models.delivery import (
    CodReconciliation,
    CodReconciliationStatus,
    DeliveryLocationLog,
    DeliveryTrip,
    DeliveryTripOrder,
    DeliveryTripOrderStatus,
    DeliveryTripStatus,
)
from app.models.finance import FinancialRecordType
from app.models.order import Order, OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.models.staff import StaffProfile
from app.models.user import User
from app.repositories import (
    delivery_repo,
    finance_repo,
    order_repo,
    payment_repo,
    staff_repo,
)
from app.schemas.delivery import (
    DeliveryBatchSuggestRequest,
    DeliveryCodReconcile,
    DeliveryLocationUpdate,
    DeliveryOrderDelivered,
    DeliveryOrderFailed,
    DeliveryQueueItem,
    DeliverySuggestedBatch,
    DeliverySuggestedStop,
    DeliveryTripCreate,
    amount_to_collect_for_order,
    payment_method_for_order,
)
from app.services import notification_service
from app.services import order_service
from app.services.errors import ServiceError
from app.services.routing_service import (
    MAX_EXACT_TSP_STOPS,
    RoutePlan,
    RouteStop,
    optimize_route_exact_tsp,
    suggest_batches_by_distance,
)

MONEY_QUANT = Decimal("0.01")
DISTANCE_QUANT = Decimal("0.001")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_delivery_queue(db: AsyncSession) -> list[DeliveryQueueItem]:
    orders = await delivery_repo.list_delivery_queue_orders(db)
    now = utc_now()
    return [_queue_item_from_order(order, now) for order in orders]


async def suggest_batches(
    db: AsyncSession,
    payload: DeliveryBatchSuggestRequest,
) -> list[DeliverySuggestedBatch]:
    queue_orders = list(await delivery_repo.list_delivery_queue_orders(db))
    if payload.order_ids:
        queue_by_id = {order.id: order for order in queue_orders}
        missing = [
            order_id for order_id in payload.order_ids if order_id not in queue_by_id
        ]
        if missing:
            raise ServiceError(
                "orders_not_available_for_delivery",
                status_code=409,
                context={"order_ids": [str(order_id) for order_id in missing]},
            )
        selected = [queue_by_id[order_id] for order_id in payload.order_ids]
        return [await _suggest_batch(selected)]

    stops = [_route_stop_from_order(order) for order in queue_orders]
    route_plans = await suggest_batches_by_distance(
        stops,
        max_orders_per_trip=payload.max_orders_per_trip,
    )
    orders_by_id = {order.id: order for order in queue_orders}
    return [
        _suggested_batch_from_route_plan(
            route_plan,
            orders_by_id=orders_by_id,
        )
        for route_plan in route_plans
    ]


async def create_trip(
    db: AsyncSession,
    payload: DeliveryTripCreate,
    *,
    current_user: User,
) -> DeliveryTrip:
    order_ids = _dedupe_order_ids(payload.order_ids)
    try:
        orders = await _validate_orders_for_trip_creation(db, order_ids)
        route_plan = (
            await _route_plan_for_orders(orders)
            if payload.use_auto_route
            else _manual_route_plan(_order_like_request(orders, order_ids))
        )
        expected_cod_amount = _sum_expected_cod(orders)
        trip_code = await delivery_repo.reserve_unique_trip_code(db)
        trip = await delivery_repo.create_trip(
            db,
            trip_code=trip_code,
            expected_cod_amount=expected_cod_amount,
            total_distance_km=Decimal(str(route_plan.total_distance_km)).quantize(
                DISTANCE_QUANT
            ),
            total_duration_minutes=route_plan.total_duration_minutes,
            route_provider=route_plan.provider,
            created_by=current_user.id,
        )
        await delivery_repo.create_trip_orders(
            db,
            trip_id=trip.id,
            route_stops=route_plan.stops,
        )
        await db.commit()
        detail = await delivery_repo.get_trip_detail(db, trip.id)
        if detail is None:
            raise ServiceError("delivery_trip_not_found", status_code=404)
        return detail
    except Exception:
        await db.rollback()
        raise


async def list_trips(
    db: AsyncSession,
    *,
    current_user: User,
    status: DeliveryTripStatus | None = None,
) -> Sequence[DeliveryTrip]:
    shipper_id: UUID | None = None
    if _role_value(current_user) == UserRole.SHIPPER.value:
        staff_profile = await _current_staff_profile(db, current_user)
        shipper_id = staff_profile.id

    return await delivery_repo.list_trips(
        db,
        status=status,
        shipper_id=shipper_id,
    )


async def get_trip(
    db: AsyncSession,
    trip_id: UUID,
    *,
    current_user: User,
) -> DeliveryTrip:
    trip = await delivery_repo.get_trip_detail(db, trip_id)
    if trip is None:
        raise ServiceError("delivery_trip_not_found", status_code=404)
    await _ensure_can_view_trip(db, current_user, trip)
    return trip


async def assign_shipper(
    db: AsyncSession,
    trip_id: UUID,
    shipper_id: UUID,
) -> DeliveryTrip:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        if trip.status != DeliveryTripStatus.PENDING_DISPATCH:
            raise ServiceError("delivery_trip_not_pending_dispatch", status_code=409)

        shipper = await staff_repo.get_staff_profile_by_id(db, shipper_id)
        if shipper is None:
            raise ServiceError("shipper_not_found", status_code=404)
        if _enum_value(shipper.role) != UserRole.SHIPPER.value:
            raise ServiceError("staff_is_not_shipper", status_code=409)
        if shipper.status != StaffStatus.ACTIVE:
            raise ServiceError("shipper_not_active", status_code=409)
        if await delivery_repo.shipper_has_active_trip(db, shipper_id):
            raise ServiceError("shipper_already_has_active_trip", status_code=409)

        now = utc_now()
        trip.shipper_id = shipper_id
        trip.status = DeliveryTripStatus.ASSIGNED
        trip.updated_at = now
        await _notify_trip_assigned(db, trip, shipper)
        await db.commit()
        return await _get_trip_detail_or_404(db, trip_id)
    except Exception:
        await db.rollback()
        raise


async def start_trip(
    db: AsyncSession,
    trip_id: UUID,
    *,
    current_user: User,
) -> DeliveryTrip:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        await _ensure_trip_actor(db, current_user, trip, allow_manager=True)
        if trip.shipper_id is None:
            raise ServiceError("delivery_trip_shipper_required", status_code=409)
        if trip.status != DeliveryTripStatus.ASSIGNED:
            raise ServiceError("delivery_trip_not_assigned", status_code=409)

        now = utc_now()
        trip.status = DeliveryTripStatus.IN_TRANSIT
        trip.started_at = now
        trip.updated_at = now
        await db.commit()
        return await _get_trip_detail_or_404(db, trip_id)
    except Exception:
        await db.rollback()
        raise


async def update_location(
    db: AsyncSession,
    trip_id: UUID,
    payload: DeliveryLocationUpdate,
    *,
    current_user: User,
) -> DeliveryLocationLog:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        staff_profile = await _ensure_trip_actor(
            db,
            current_user,
            trip,
            allow_manager=False,
        )
        if trip.status != DeliveryTripStatus.IN_TRANSIT:
            raise ServiceError("delivery_trip_not_in_transit", status_code=409)

        log = await delivery_repo.create_location_log(
            db,
            trip_id=trip.id,
            shipper_id=staff_profile.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            recorded_at=utc_now(),
        )
        await db.commit()
        return log
    except Exception:
        await db.rollback()
        raise


async def mark_order_delivered(
    db: AsyncSession,
    trip_id: UUID,
    order_id: UUID,
    payload: DeliveryOrderDelivered,
    *,
    current_user: User,
) -> DeliveryTrip:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        await _ensure_trip_actor(db, current_user, trip, allow_manager=False)
        if trip.status != DeliveryTripStatus.IN_TRANSIT:
            raise ServiceError("delivery_trip_not_in_transit", status_code=409)

        trip_order = await _get_trip_order_or_404(db, trip_id, order_id)
        if trip_order.status != DeliveryTripOrderStatus.ASSIGNED:
            raise ServiceError("delivery_order_not_assigned", status_code=409)

        order = trip_order.order
        await _handle_delivery_payment(
            db,
            order,
            cod_collected=payload.cod_collected,
            actor_user_id=current_user.id,
        )

        now = utc_now()
        trip_order.status = DeliveryTripOrderStatus.DELIVERED
        trip_order.cod_collected = payload.cod_collected.quantize(MONEY_QUANT)
        trip_order.delivered_at = now
        trip_order.note = payload.note
        trip_order.updated_at = now
        await db.flush()

        if order.status != OrderStatus.COMPLETED:
            await order_service.complete_order_without_commit(db, order.id)

        await _complete_trip_when_all_stops_final(db, trip)
        await _notify_delivery_order_delivered(db, trip, trip_order)
        await db.commit()
        return await _get_trip_detail_or_404(db, trip_id)
    except Exception:
        await db.rollback()
        raise


async def mark_order_failed(
    db: AsyncSession,
    trip_id: UUID,
    order_id: UUID,
    payload: DeliveryOrderFailed,
    *,
    current_user: User,
) -> DeliveryTrip:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        await _ensure_trip_actor(db, current_user, trip, allow_manager=False)
        if trip.status != DeliveryTripStatus.IN_TRANSIT:
            raise ServiceError("delivery_trip_not_in_transit", status_code=409)

        trip_order = await _get_trip_order_or_404(db, trip_id, order_id)
        if trip_order.status != DeliveryTripOrderStatus.ASSIGNED:
            raise ServiceError("delivery_order_not_assigned", status_code=409)

        now = utc_now()
        trip_order.status = DeliveryTripOrderStatus.FAILED
        trip_order.failed_at = now
        trip_order.failed_reason = payload.failed_reason
        trip_order.note = payload.note
        trip_order.updated_at = now
        await order_repo.update_order_status(
            db,
            trip_order.order,
            status=OrderStatus.READY_FOR_DELIVERY,
        )
        await db.flush()

        await _complete_trip_when_all_stops_final(db, trip)
        await _notify_delivery_order_failed(db, trip, trip_order)
        await db.commit()
        return await _get_trip_detail_or_404(db, trip_id)
    except Exception:
        await db.rollback()
        raise


async def complete_trip(
    db: AsyncSession,
    trip_id: UUID,
    *,
    current_user: User,
) -> DeliveryTrip:
    try:
        trip = await _get_trip_for_update_or_404(db, trip_id)
        await _ensure_trip_actor(db, current_user, trip, allow_manager=True)
        if trip.status not in (
            DeliveryTripStatus.ASSIGNED,
            DeliveryTripStatus.IN_TRANSIT,
        ):
            raise ServiceError("delivery_trip_cannot_be_completed", status_code=409)

        trip_orders = await delivery_repo.list_trip_orders(db, trip.id)
        if not trip_orders or not _all_stops_final(trip_orders):
            raise ServiceError("delivery_trip_has_unfinished_orders", status_code=409)

        now = utc_now()
        trip.status = DeliveryTripStatus.COMPLETED
        trip.completed_at = now
        trip.updated_at = now
        await _notify_trip_completed(db, trip)
        await db.commit()
        return await _get_trip_detail_or_404(db, trip_id)
    except Exception:
        await db.rollback()
        raise


async def reconcile_cod(
    db: AsyncSession,
    trip_id: UUID,
    payload: DeliveryCodReconcile,
    *,
    current_user: User,
) -> CodReconciliation:
    try:
        trip = await _get_trip_detail_or_404(db, trip_id)
        if trip.status != DeliveryTripStatus.COMPLETED:
            raise ServiceError("delivery_trip_not_completed", status_code=409)
        if trip.shipper_id is None:
            raise ServiceError("delivery_trip_shipper_required", status_code=409)
        if await delivery_repo.get_reconciliation_by_trip(db, trip_id) is not None:
            raise ServiceError("cod_already_reconciled", status_code=409)

        expected_amount = sum(
            (
                trip_order.cod_collected
                for trip_order in trip.trip_orders
                if trip_order.status == DeliveryTripOrderStatus.DELIVERED
            ),
            Decimal("0"),
        ).quantize(MONEY_QUANT)
        discrepancy = (payload.actual_amount - expected_amount).quantize(MONEY_QUANT)
        if discrepancy != Decimal("0") and not payload.discrepancy_reason:
            raise ServiceError("cod_discrepancy_reason_required", status_code=422)

        status = (
            CodReconciliationStatus.FLAGGED_FOR_REVIEW
            if discrepancy != Decimal("0")
            else CodReconciliationStatus.CONFIRMED
        )
        reconciled_at = utc_now()
        reconciliation = await delivery_repo.create_reconciliation(
            db,
            trip_id=trip.id,
            shipper_id=trip.shipper_id,
            expected_amount=expected_amount,
            actual_amount=payload.actual_amount,
            discrepancy_amount=discrepancy,
            discrepancy_reason=payload.discrepancy_reason,
            status=status,
            reconciled_by=current_user.id,
            reconciled_at=reconciled_at,
        )

        trip.actual_cod_amount = payload.actual_amount
        trip.discrepancy_amount = discrepancy
        trip.discrepancy_reason = payload.discrepancy_reason
        trip.status = DeliveryTripStatus.RECONCILED
        trip.reconciled_at = reconciled_at
        trip.updated_at = reconciled_at

        if discrepancy != Decimal("0"):
            await finance_repo.create_financial_record(
                db,
                record_type=FinancialRecordType.COD_RECONCILIATION,
                source_type="cod_reconciliation",
                source_id=reconciliation.id,
                amount=abs(discrepancy),
                record_date=reconciled_at.date(),
                locked=True,
            )
            await _notify_cod_discrepancy(
                db,
                trip,
                expected_amount=expected_amount,
                actual_amount=payload.actual_amount,
                discrepancy=discrepancy,
            )

        await db.commit()
        await db.refresh(reconciliation)
        return reconciliation
    except Exception:
        await db.rollback()
        raise


async def _notify_trip_assigned(
    db: AsyncSession,
    trip: DeliveryTrip,
    shipper: StaffProfile,
) -> None:
    trip_code = getattr(trip, "trip_code", str(trip.id))
    await notification_service.notify_user(
        db,
        shipper.user_id,
        notification_type="delivery.trip_assigned",
        title="New delivery trip assigned",
        message=f"Trip {trip_code} has been assigned to you.",
        entity_type="delivery_trip",
        entity_id=trip.id,
        action_url="shipper.html",
        metadata={
            "trip_code": trip_code,
            "shipper_id": str(shipper.id),
        },
        dedupe_key=f"delivery.trip_assigned:{trip.id}:{shipper.user_id}",
    )


async def _notify_delivery_order_failed(
    db: AsyncSession,
    trip: DeliveryTrip,
    trip_order: DeliveryTripOrder,
) -> None:
    order = trip_order.order
    trip_code = getattr(trip, "trip_code", str(trip.id))
    await notification_service.notify_roles(
        db,
        (UserRole.ADMIN, UserRole.DELIVERY_MANAGER),
        notification_type="delivery.order_failed",
        title="Delivery order failed",
        message=f"Order {order.order_code} failed during trip {trip_code}.",
        severity="warning",
        entity_type="order",
        entity_id=order.id,
        action_url="delivery_manage.html",
        metadata={
            "trip_id": str(trip.id),
            "trip_code": trip_code,
            "order_code": order.order_code,
            "failed_reason": trip_order.failed_reason,
        },
        dedupe_key=f"delivery.order_failed:{trip.id}:{order.id}",
    )


async def _notify_delivery_order_delivered(
    db: AsyncSession,
    trip: DeliveryTrip,
    trip_order: DeliveryTripOrder,
) -> None:
    order = trip_order.order
    trip_code = getattr(trip, "trip_code", str(trip.id))

    await notification_service.notify_roles(
        db,
        (UserRole.DELIVERY_MANAGER,),
        notification_type="delivery.order_delivered",
        title="Delivery order completed",
        message=f"Order {order.order_code} was delivered in trip {trip_code}.",
        entity_type="order",
        entity_id=order.id,
        action_url="delivery_manage.html",
        metadata={
            "trip_id": str(trip.id),
            "trip_code": trip_code,
            "order_code": order.order_code,
            "cod_collected": str(trip_order.cod_collected),
        },
        dedupe_key=f"delivery.order_delivered:{trip.id}:{order.id}",
    )


async def _notify_trip_completed(
    db: AsyncSession,
    trip: DeliveryTrip,
) -> None:
    trip_code = getattr(trip, "trip_code", str(trip.id))
    await notification_service.notify_roles(
        db,
        (UserRole.DELIVERY_MANAGER,),
        notification_type="delivery.trip_completed",
        title="Delivery trip completed",
        message=f"Trip {trip_code} is completed. The assigned shipper is available.",
        entity_type="delivery_trip",
        entity_id=trip.id,
        action_url="delivery_manage.html",
        metadata={
            "trip_id": str(trip.id),
            "trip_code": trip_code,
            "shipper_id": str(trip.shipper_id) if trip.shipper_id else None,
        },
        dedupe_key=f"delivery.trip_completed:{trip.id}",
    )


async def _notify_cod_discrepancy(
    db: AsyncSession,
    trip: DeliveryTrip,
    *,
    expected_amount: Decimal,
    actual_amount: Decimal,
    discrepancy: Decimal,
) -> None:
    trip_code = getattr(trip, "trip_code", str(trip.id))
    await notification_service.notify_roles(
        db,
        (UserRole.ADMIN, UserRole.DELIVERY_MANAGER),
        notification_type="delivery.cod_discrepancy",
        title="COD discrepancy flagged",
        message=f"Trip {trip_code} has a COD discrepancy of {discrepancy}.",
        severity="critical",
        entity_type="delivery_trip",
        entity_id=trip.id,
        action_url="delivery_manage.html",
        metadata={
            "trip_code": trip_code,
            "expected_amount": str(expected_amount),
            "actual_amount": str(actual_amount),
            "discrepancy": str(discrepancy),
        },
        dedupe_key=f"delivery.cod_discrepancy:{trip.id}",
    )


def _queue_item_from_order(order: Order, now: datetime) -> DeliveryQueueItem:
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return DeliveryQueueItem(
        order_id=order.id,
        order_code=order.order_code,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        delivery_address=order.delivery_address,
        delivery_latitude=order.delivery_latitude,
        delivery_longitude=order.delivery_longitude,
        geocoding_status=getattr(order, "geocoding_status", None),
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        payment_method=payment_method_for_order(order),
        amount_to_collect=amount_to_collect_for_order(order),
        waiting_time=_format_waiting_time(now - created_at),
        created_at=created_at,
    )


async def _suggest_batch(orders: list[Order]) -> DeliverySuggestedBatch:
    route_plan = await _route_plan_for_orders(orders)
    orders_by_id = {order.id: order for order in orders}
    return _suggested_batch_from_route_plan(route_plan, orders_by_id=orders_by_id)


def _suggested_batch_from_route_plan(
    route_plan: RoutePlan,
    *,
    orders_by_id: dict[UUID, Order],
) -> DeliverySuggestedBatch:
    suggested_stops = [
        DeliverySuggestedStop(
            order_id=stop.order_id,
            order_code=orders_by_id[stop.order_id].order_code,
            stop_order=stop.stop_order,
            distance_from_previous_km=stop.distance_from_previous_km,
            duration_from_previous_minutes=stop.duration_from_previous_minutes,
        )
        for stop in route_plan.stops
    ]
    return DeliverySuggestedBatch(
        orders=suggested_stops,
        total_distance_km=route_plan.total_distance_km,
        total_duration_minutes=route_plan.total_duration_minutes,
        route_provider=route_plan.provider,
        expected_cod_amount=_sum_expected_cod(
            [orders_by_id[stop.order_id] for stop in route_plan.stops]
        ),
    )


def _route_stop_from_order(order: Order) -> RouteStop:
    if order.delivery_latitude is None or order.delivery_longitude is None:
        raise ServiceError(
            "delivery_coordinates_required",
            status_code=409,
            context={"order_id": str(order.id)},
        )
    return RouteStop(
        order_id=order.id,
        latitude=order.delivery_latitude,
        longitude=order.delivery_longitude,
        created_at=order.created_at,
    )


async def _route_plan_for_orders(orders: list[Order]) -> RoutePlan:
    if len(orders) > MAX_EXACT_TSP_STOPS:
        raise ServiceError(
            "delivery_batch_too_large_for_exact_tsp",
            status_code=422,
            context={"max_orders_per_trip": MAX_EXACT_TSP_STOPS},
        )
    return await optimize_route_exact_tsp(
        [_route_stop_from_order(order) for order in orders]
    )


def _manual_route_plan(orders: list[Order]) -> RoutePlan:
    stops: list[RouteStop] = []
    for index, order in enumerate(orders, start=1):
        stop = _route_stop_from_order(order)
        stops.append(
            RouteStop(
                order_id=stop.order_id,
                latitude=stop.latitude,
                longitude=stop.longitude,
                created_at=stop.created_at,
                stop_order=index,
                distance_from_previous_km=0.0,
                duration_from_previous_minutes=0,
            )
        )
    return RoutePlan(
        stops=stops,
        total_distance_km=0.0,
        total_duration_minutes=0,
        provider="manual",
    )


async def _validate_orders_for_trip_creation(
    db: AsyncSession,
    order_ids: list[UUID],
) -> list[Order]:
    orders = list(await delivery_repo.get_orders_by_ids_for_update(db, order_ids))
    orders_by_id = {order.id: order for order in orders}
    missing = [order_id for order_id in order_ids if order_id not in orders_by_id]
    if missing:
        raise ServiceError(
            "orders_not_found",
            status_code=404,
            context={"order_ids": [str(order_id) for order_id in missing]},
        )

    ordered = [orders_by_id[order_id] for order_id in order_ids]
    for order in ordered:
        _validate_order_for_trip(order)
        if await delivery_repo.order_has_active_assignment(db, order.id):
            raise ServiceError(
                "order_already_assigned_to_active_trip",
                status_code=409,
                context={"order_id": str(order.id)},
            )
        _route_stop_from_order(order)
    return ordered


def _validate_order_for_trip(order: Order) -> None:
    if order.order_type != OrderType.DELIVERY:
        raise ServiceError(
            "order_is_not_delivery",
            status_code=409,
            context={"order_id": str(order.id)},
        )
    if order.status != OrderStatus.READY_FOR_DELIVERY:
        raise ServiceError(
            "order_not_ready_for_delivery",
            status_code=409,
            context={"order_id": str(order.id)},
        )


def _order_like_request(orders: list[Order], order_ids: list[UUID]) -> list[Order]:
    orders_by_id = {order.id: order for order in orders}
    return [orders_by_id[order_id] for order_id in order_ids]


def _dedupe_order_ids(order_ids: list[UUID]) -> list[UUID]:
    deduped = list(dict.fromkeys(order_ids))
    if len(deduped) != len(order_ids):
        raise ServiceError("duplicate_order_ids", status_code=422)
    return deduped


def _sum_expected_cod(orders: Sequence[Order]) -> Decimal:
    return sum((_cod_amount(order) for order in orders), Decimal("0")).quantize(
        MONEY_QUANT
    )


def _cod_amount(order: Order) -> Decimal:
    if order.payment_status == OrderPaymentStatus.UNPAID:
        return order.total_amount.quantize(MONEY_QUANT)
    return Decimal("0.00")


def _format_waiting_time(delta) -> str:
    total_minutes = max(int(delta.total_seconds() // 60), 0)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours} hours {minutes} minutes"
    return f"{minutes} minutes"


async def _get_trip_detail_or_404(
    db: AsyncSession,
    trip_id: UUID,
) -> DeliveryTrip:
    trip = await delivery_repo.get_trip_detail(db, trip_id)
    if trip is None:
        raise ServiceError("delivery_trip_not_found", status_code=404)
    return trip


async def _get_trip_for_update_or_404(
    db: AsyncSession,
    trip_id: UUID,
) -> DeliveryTrip:
    trip = await delivery_repo.get_trip_for_update(db, trip_id)
    if trip is None:
        raise ServiceError("delivery_trip_not_found", status_code=404)
    return trip


async def _get_trip_order_or_404(
    db: AsyncSession,
    trip_id: UUID,
    order_id: UUID,
) -> DeliveryTripOrder:
    trip_order = await delivery_repo.get_trip_order_detail(
        db,
        trip_id=trip_id,
        order_id=order_id,
    )
    if trip_order is None:
        raise ServiceError("delivery_order_not_found_in_trip", status_code=404)
    return trip_order


async def _ensure_can_view_trip(
    db: AsyncSession,
    current_user: User,
    trip: DeliveryTrip,
) -> None:
    if _is_manager(current_user):
        return
    await _ensure_trip_actor(db, current_user, trip, allow_manager=False)


async def _ensure_trip_actor(
    db: AsyncSession,
    current_user: User,
    trip: DeliveryTrip,
    *,
    allow_manager: bool,
) -> StaffProfile:
    if allow_manager and _is_manager(current_user):
        if trip.shipper_id is not None:
            shipper = await staff_repo.get_staff_profile_by_id(db, trip.shipper_id)
            if shipper is not None:
                return shipper
        raise ServiceError("delivery_trip_shipper_required", status_code=409)

    staff_profile = await _current_staff_profile(db, current_user)
    if trip.shipper_id != staff_profile.id:
        raise ServiceError(
            "delivery_trip_not_assigned_to_current_shipper",
            status_code=403,
        )
    return staff_profile


async def _current_staff_profile(
    db: AsyncSession,
    current_user: User,
) -> StaffProfile:
    staff_profile = await staff_repo.get_staff_profile_by_user_id(db, current_user.id)
    if staff_profile is None:
        raise ServiceError("current_user_staff_profile_not_found", status_code=403)
    if _enum_value(staff_profile.role) != UserRole.SHIPPER.value:
        raise ServiceError("current_user_is_not_shipper", status_code=403)
    return staff_profile


def _is_manager(user: User) -> bool:
    return _role_value(user) in {UserRole.ADMIN.value, UserRole.DELIVERY_MANAGER.value}


def _role_value(user: User) -> str:
    return _enum_value(user.role)


def _enum_value(value) -> str:
    return getattr(value, "value", value)


async def _handle_delivery_payment(
    db: AsyncSession,
    order: Order,
    *,
    cod_collected: Decimal,
    actor_user_id: UUID,
) -> None:
    requires_cod = order.payment_status == OrderPaymentStatus.UNPAID or any(
        payment.method == PaymentMethod.COD for payment in order.payments
    )
    cod_collected = cod_collected.quantize(MONEY_QUANT)

    if not requires_cod:
        if cod_collected != Decimal("0.00"):
            raise ServiceError("cod_not_expected_for_paid_order", status_code=409)
        return

    expected = order.total_amount.quantize(MONEY_QUANT)
    if cod_collected != expected:
        raise ServiceError(
            "cod_collected_must_equal_order_total",
            status_code=409,
            context={
                "expected": str(expected),
                "actual": str(cod_collected),
            },
        )

    if expected > Decimal("0"):
        pending_cod = await payment_repo.get_pending_cod_payment_for_order(
            db,
            order.id,
        )
        if pending_cod is not None:
            pending_cod.amount = expected
            await payment_repo.mark_payment_success(
                db,
                pending_cod,
                amount_received=cod_collected,
                paid_at=utc_now(),
            )
        else:
            await payment_repo.create_payment_event(
                db,
                order_id=order.id,
                method=PaymentMethod.COD,
                status=PaymentEventStatus.SUCCESS,
                amount=expected,
                amount_received=cod_collected,
                change_amount=Decimal("0.00"),
                paid_at=utc_now(),
                created_by=actor_user_id,
            )

    await order_repo.update_order_status(
        db,
        order,
        payment_status=OrderPaymentStatus.PAID,
    )


async def _complete_trip_when_all_stops_final(
    db: AsyncSession,
    trip: DeliveryTrip,
) -> None:
    trip_orders = await delivery_repo.list_trip_orders(db, trip.id)
    if _all_stops_final(trip_orders) and trip.status != DeliveryTripStatus.COMPLETED:
        now = utc_now()
        trip.status = DeliveryTripStatus.COMPLETED
        trip.completed_at = now
        trip.updated_at = now
        await _notify_trip_completed(db, trip)


def _all_stops_final(trip_orders: Sequence[DeliveryTripOrder]) -> bool:
    return all(
        trip_order.status
        in (DeliveryTripOrderStatus.DELIVERED, DeliveryTripOrderStatus.FAILED)
        for trip_order in trip_orders
    )
