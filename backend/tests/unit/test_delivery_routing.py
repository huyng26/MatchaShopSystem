from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.errors import ServiceError
from app.services.routing_service import (
    RouteStop,
    exact_tsp_order,
    order_stops_nearest_neighbor,
    suggest_batches_by_distance,
)
from app.utils.distance import haversine_distance_km


def test_haversine_distance_km_returns_reasonable_hcm_distance() -> None:
    distance = haversine_distance_km(10.776889, 106.700806, 10.7829, 106.6934)

    assert 1.0 < distance < 1.2


def test_order_stops_nearest_neighbor_orders_by_next_closest_stop() -> None:
    first_id = uuid4()
    second_id = uuid4()
    far_id = uuid4()
    stops = [
        RouteStop(far_id, Decimal("10.9000000"), Decimal("106.9000000")),
        RouteStop(second_id, Decimal("10.7820000"), Decimal("106.7060000")),
        RouteStop(first_id, Decimal("10.7780000"), Decimal("106.7020000")),
    ]

    ordered = order_stops_nearest_neighbor(
        stops,
        shop_latitude=10.776889,
        shop_longitude=106.700806,
    )

    assert [stop.order_id for stop in ordered] == [first_id, second_id, far_id]
    assert [stop.stop_order for stop in ordered] == [1, 2, 3]
    assert all(stop.distance_from_previous_km >= 0 for stop in ordered)


def test_exact_tsp_order_picks_lowest_duration_route() -> None:
    # Matrix indexes: 0 = shop, 1..3 = stops. Best route is stop 2 -> 3 -> 1.
    duration = [
        [0, 8, 2, 9],
        [8, 0, 7, 2],
        [2, 7, 0, 3],
        [9, 2, 3, 0],
    ]
    distance = [
        [0.0, 8.0, 2.0, 9.0],
        [8.0, 0.0, 7.0, 2.0],
        [2.0, 7.0, 0.0, 3.0],
        [9.0, 2.0, 3.0, 0.0],
    ]

    assert exact_tsp_order(duration_minutes=duration, distance_km=distance) == [
        1,
        2,
        0,
    ]


@pytest.mark.asyncio
async def test_suggest_batches_by_distance_respects_max_orders_per_trip() -> None:
    stops = [
        RouteStop(uuid4(), Decimal("10.7700000"), Decimal("106.7000000")),
        RouteStop(uuid4(), Decimal("10.7710000"), Decimal("106.7010000")),
        RouteStop(uuid4(), Decimal("10.9000000"), Decimal("106.9000000")),
    ]

    batches = await suggest_batches_by_distance(stops, max_orders_per_trip=2)

    assert [len(batch.stops) for batch in batches] == [2, 1]


@pytest.mark.asyncio
async def test_suggest_batches_rejects_more_than_twelve_stops() -> None:
    stops = [
        RouteStop(uuid4(), Decimal("10.7700000"), Decimal("106.7000000")),
    ]

    with pytest.raises(ServiceError) as error:
        await suggest_batches_by_distance(stops, max_orders_per_trip=13)

    assert error.value.code == "max_orders_per_trip_exceeds_exact_tsp_limit"
