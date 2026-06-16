def test_notification_routes_are_registered() -> None:
    from app.main import app

    paths = {route.path for route in app.routes}

    assert "/api/v1/notifications" in paths
    assert "/api/v1/notifications/unread-count" in paths
    assert "/api/v1/notifications/{notification_id}/read" in paths
    assert "/api/v1/notifications/read-all" in paths
