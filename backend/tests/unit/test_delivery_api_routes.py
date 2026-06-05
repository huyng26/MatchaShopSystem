from app.main import app


def test_delivery_and_shipper_routes_follow_delivery_plan() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/orders/{order_id}/start-processing" in paths
    assert "/api/v1/orders/{order_id}/ready-for-delivery" in paths

    assert "/api/v1/deliveries/trips/{trip_id}/complete" not in paths
    assert "/api/v1/deliveries/trips/{trip_id}/start" not in paths
    assert "/api/v1/deliveries/trips/{trip_id}/location" not in paths
    assert (
        "/api/v1/deliveries/trips/{trip_id}/orders/{order_id}/delivered"
        not in paths
    )
    assert "/api/v1/deliveries/trips/{trip_id}/orders/{order_id}/failed" not in paths

    assert "/api/v1/shipper/trips" in paths
    assert "/api/v1/shipper/trips/{trip_id}" in paths
    assert "/api/v1/shipper/trips/{trip_id}/start" in paths
    assert "/api/v1/shipper/trips/{trip_id}/location" in paths
    assert "/api/v1/shipper/trips/{trip_id}/orders/{order_id}/delivered" in paths
    assert "/api/v1/shipper/trips/{trip_id}/orders/{order_id}/failed" in paths
