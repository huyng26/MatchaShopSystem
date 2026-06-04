from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.utils.distance import haversine_distance_km


@dataclass(frozen=True)
class RouteStop:
    order_id: UUID
    latitude: Decimal
    longitude: Decimal
    stop_order: int = 0
    distance_from_previous_km: float = 0.0


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
                stop_order=len(ordered) + 1,
                distance_from_previous_km=round(distance, 3),
            )
        )
        current_lat = float(next_stop.latitude)
        current_lon = float(next_stop.longitude)

    return ordered


def suggest_batches_by_distance(
    stops: list[RouteStop],
    *,
    max_orders_per_trip: int,
) -> list[list[RouteStop]]:
    if max_orders_per_trip <= 0:
        raise ValueError("max_orders_per_trip must be positive")

    ordered = order_stops_nearest_neighbor(
        stops,
        shop_latitude=float(stops[0].latitude) if stops else 0.0,
        shop_longitude=float(stops[0].longitude) if stops else 0.0,
    )
    return [
        ordered[index : index + max_orders_per_trip]
        for index in range(0, len(ordered), max_orders_per_trip)
    ]
