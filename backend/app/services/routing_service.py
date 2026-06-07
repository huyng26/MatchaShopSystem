from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.core.config import get_settings
from app.services import map_service
from app.services.errors import ServiceError
from app.utils.distance import haversine_distance_km

MAX_EXACT_TSP_STOPS = 12


@dataclass(frozen=True)
class RouteStop:
    order_id: UUID
    latitude: Decimal
    longitude: Decimal
    created_at: datetime | None = None
    stop_order: int = 0
    distance_from_previous_km: float = 0.0
    duration_from_previous_minutes: int = 0


@dataclass(frozen=True)
class RoutePlan:
    stops: list[RouteStop]
    total_distance_km: float
    total_duration_minutes: int
    provider: str


async def optimize_route_exact_tsp(
    stops: list[RouteStop],
    *,
    shop_latitude: float | None = None,
    shop_longitude: float | None = None,
) -> RoutePlan:
    if len(stops) > MAX_EXACT_TSP_STOPS:
        raise ServiceError(
            "delivery_batch_too_large_for_exact_tsp",
            status_code=422,
            context={"max_orders_per_trip": MAX_EXACT_TSP_STOPS},
        )
    if not stops:
        return RoutePlan([], 0.0, 0, _route_provider())

    settings = get_settings()
    shop_latitude = settings.shop_latitude if shop_latitude is None else shop_latitude
    shop_longitude = (
        settings.shop_longitude if shop_longitude is None else shop_longitude
    )
    coordinates = [
        map_service.Coordinate(
            latitude=Decimal(str(shop_latitude)),
            longitude=Decimal(str(shop_longitude)),
        ),
        *[
            map_service.Coordinate(
                latitude=stop.latitude,
                longitude=stop.longitude,
            )
            for stop in stops
        ],
    ]
    matrix = await map_service.build_route_matrix(coordinates)
    order = exact_tsp_order(
        duration_minutes=matrix.duration_minutes,
        distance_km=matrix.distance_km,
    )

    ordered: list[RouteStop] = []
    total_distance = 0.0
    total_duration = 0
    previous_index = 0
    for stop_order, stop_index in enumerate(order, start=1):
        matrix_index = stop_index + 1
        distance = matrix.distance_km[previous_index][matrix_index]
        duration = matrix.duration_minutes[previous_index][matrix_index]
        total_distance += distance
        total_duration += duration
        stop = stops[stop_index]
        ordered.append(
            RouteStop(
                order_id=stop.order_id,
                latitude=stop.latitude,
                longitude=stop.longitude,
                created_at=stop.created_at,
                stop_order=stop_order,
                distance_from_previous_km=round(distance, 3),
                duration_from_previous_minutes=duration,
            )
        )
        previous_index = matrix_index

    return RoutePlan(
        stops=ordered,
        total_distance_km=round(total_distance, 3),
        total_duration_minutes=total_duration,
        provider=matrix.provider,
    )


def exact_tsp_order(
    *,
    duration_minutes: list[list[int]],
    distance_km: list[list[float]],
) -> list[int]:
    stop_count = len(duration_minutes) - 1
    if stop_count <= 0:
        return []
    if stop_count > MAX_EXACT_TSP_STOPS:
        raise ServiceError(
            "delivery_batch_too_large_for_exact_tsp",
            status_code=422,
            context={"max_orders_per_trip": MAX_EXACT_TSP_STOPS},
        )
    _validate_matrix(duration_minutes, stop_count + 1)
    _validate_matrix(distance_km, stop_count + 1)

    dp: dict[tuple[int, int], tuple[int, float]] = {}
    parent: dict[tuple[int, int], int | None] = {}
    for stop_index in range(stop_count):
        mask = 1 << stop_index
        matrix_index = stop_index + 1
        dp[(mask, stop_index)] = (
            duration_minutes[0][matrix_index],
            distance_km[0][matrix_index],
        )
        parent[(mask, stop_index)] = None

    for mask in range(1, 1 << stop_count):
        for last in range(stop_count):
            current = dp.get((mask, last))
            if current is None:
                continue
            for next_stop in range(stop_count):
                bit = 1 << next_stop
                if mask & bit:
                    continue
                next_mask = mask | bit
                from_index = last + 1
                to_index = next_stop + 1
                candidate = (
                    current[0] + duration_minutes[from_index][to_index],
                    current[1] + distance_km[from_index][to_index],
                )
                key = (next_mask, next_stop)
                if key not in dp or candidate < dp[key]:
                    dp[key] = candidate
                    parent[key] = last

    full_mask = (1 << stop_count) - 1
    best_last = min(
        range(stop_count),
        key=lambda stop_index: dp[(full_mask, stop_index)],
    )
    reversed_order: list[int] = []
    key = (full_mask, best_last)
    while True:
        mask, last = key
        reversed_order.append(last)
        previous = parent[key]
        if previous is None:
            break
        key = (mask ^ (1 << last), previous)

    return list(reversed(reversed_order))


async def suggest_batches_by_distance(
    stops: list[RouteStop],
    *,
    max_orders_per_trip: int,
) -> list[RoutePlan]:
    if max_orders_per_trip <= 0:
        raise ServiceError("max_orders_per_trip_must_be_positive", status_code=422)
    if max_orders_per_trip > MAX_EXACT_TSP_STOPS:
        raise ServiceError(
            "max_orders_per_trip_exceeds_exact_tsp_limit",
            status_code=422,
            context={"max_orders_per_trip": MAX_EXACT_TSP_STOPS},
        )

    batches = _cluster_stops(stops, max_orders_per_trip=max_orders_per_trip)
    return [await optimize_route_exact_tsp(batch) for batch in batches]


def _cluster_stops(
    stops: list[RouteStop],
    *,
    max_orders_per_trip: int,
) -> list[list[RouteStop]]:
    remaining = list(stops)
    batches: list[list[RouteStop]] = []
    now = datetime.now(timezone.utc)

    while remaining:
        seed = min(remaining, key=_created_at_or_now)
        remaining.remove(seed)
        batch = [seed]

        while remaining and len(batch) < max_orders_per_trip:
            next_stop = min(
                remaining,
                key=lambda stop: _batch_candidate_score(stop, seed, now),
            )
            remaining.remove(next_stop)
            batch.append(next_stop)

        batches.append(batch)

    return batches


def _batch_candidate_score(stop: RouteStop, seed: RouteStop, now: datetime) -> float:
    distance = haversine_distance_km(
        float(seed.latitude),
        float(seed.longitude),
        float(stop.latitude),
        float(stop.longitude),
    )
    created_at = _created_at_or_now(stop)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    waiting_hours = max((now - created_at).total_seconds() / 3600, 0)
    waiting_bonus = min(waiting_hours, 6) * 0.35
    return distance - waiting_bonus


def _created_at_or_now(stop: RouteStop) -> datetime:
    if stop.created_at is None:
        return datetime.now(timezone.utc)
    if stop.created_at.tzinfo is None:
        return stop.created_at.replace(tzinfo=timezone.utc)
    return stop.created_at


def _validate_matrix(matrix: list[list[object]], expected_size: int) -> None:
    if len(matrix) != expected_size or any(len(row) != expected_size for row in matrix):
        raise ServiceError("route_matrix_invalid_shape", status_code=422)


def _route_provider() -> str:
    settings = get_settings()
    return settings.maps_provider


def order_stops_nearest_neighbor(
    stops: list[RouteStop],
    *,
    shop_latitude: float,
    shop_longitude: float,
) -> list[RouteStop]:
    remaining = list(stops)
    ordered: list[RouteStop] = []
    current_lat = shop_latitude
    current_lon = shop_longitude

    while remaining:
        next_stop, distance = min(
            (
                (
                    stop,
                    haversine_distance_km(
                        current_lat,
                        current_lon,
                        float(stop.latitude),
                        float(stop.longitude),
                    ),
                )
                for stop in remaining
            ),
            key=lambda item: item[1],
        )
        remaining.remove(next_stop)
        ordered.append(
            RouteStop(
                order_id=next_stop.order_id,
                latitude=next_stop.latitude,
                longitude=next_stop.longitude,
                created_at=next_stop.created_at,
                stop_order=len(ordered) + 1,
                distance_from_previous_km=round(distance, 3),
            )
        )
        current_lat = float(next_stop.latitude)
        current_lon = float(next_stop.longitude)

    return ordered
