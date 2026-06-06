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


def test_dashboard_routes_follow_dashboard_plan() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/dashboard/today" in paths
    assert "/api/v1/dashboard/low-stock" in paths
    assert "/api/v1/dashboard/best-selling-products" in paths
    assert "/api/v1/dashboard/delivery-performance" in paths
    assert "month" in {
        parameter["name"]
        for parameter in paths["/api/v1/dashboard/best-selling-products"]["get"][
            "parameters"
        ]
    }
    assert "month" in {
        parameter["name"]
        for parameter in paths["/api/v1/dashboard/delivery-performance"]["get"][
            "parameters"
        ]
    }
    assert paths["/api/v1/dashboard/today"]["get"]["security"]
    assert paths["/api/v1/dashboard/low-stock"]["get"]["security"]
    assert paths["/api/v1/dashboard/best-selling-products"]["get"]["security"]
    assert paths["/api/v1/dashboard/delivery-performance"]["get"]["security"]
