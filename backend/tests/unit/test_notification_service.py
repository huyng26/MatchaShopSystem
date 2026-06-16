from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.constants import UserRole
from app.services import delivery_service
from app.services import notification_service
from app.services import order_service
from app.services.errors import ServiceError


class FakeDb:
    async def execute(self, *_args, **_kwargs):
        return None

    async def commit(self):
        return None

    async def rollback(self):
        return None


@pytest.mark.asyncio
async def test_notify_roles_creates_one_row_per_active_user(monkeypatch):
    db = FakeDb()
    admin_id = uuid4()
    manager_id = uuid4()
    captured = {}

    async def list_active_user_ids_by_roles(db, roles):
        captured["roles"] = tuple(roles)
        return [admin_id, manager_id, admin_id]

    async def create_notifications(db, rows):
        captured["rows"] = rows

    monkeypatch.setattr(
        notification_service.notification_repo,
        "list_active_user_ids_by_roles",
        list_active_user_ids_by_roles,
    )
    monkeypatch.setattr(
        notification_service.notification_repo,
        "create_notifications",
        create_notifications,
    )

    await notification_service.notify_roles(
        db,
        (UserRole.ADMIN, UserRole.DELIVERY_MANAGER),
        notification_type="order.ready_for_delivery",
        title="Ready",
        message="Order is ready",
        entity_type="order",
        entity_id=uuid4(),
        action_url="delivery_manage.html",
        dedupe_key="order.ready:test",
    )

    assert captured["roles"] == (UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    assert [row["user_id"] for row in captured["rows"]] == [admin_id, manager_id]
    assert captured["rows"][0]["type"] == "order.ready_for_delivery"
    assert captured["rows"][0]["action_url"] == "delivery_manage.html"
    assert captured["rows"][0]["dedupe_key"] == "order.ready:test"
    assert captured["rows"][0]["metadata"] == {}


@pytest.mark.asyncio
async def test_notify_user_rejects_invalid_severity(monkeypatch):
    async def create_notifications(db, rows):
        raise AssertionError("should not create notification")

    monkeypatch.setattr(
        notification_service.notification_repo,
        "create_notifications",
        create_notifications,
    )

    with pytest.raises(ServiceError) as error:
        await notification_service.notify_user(
            FakeDb(),
            uuid4(),
            notification_type="test",
            title="Bad",
            message="Bad severity",
            severity="urgent",
        )

    assert error.value.code == "notification_severity_invalid"


@pytest.mark.asyncio
async def test_mark_read_scopes_to_current_user(monkeypatch):
    db = FakeDb()
    notification = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        read_at=datetime.now(timezone.utc),
    )
    captured = {}

    async def mark_read(db, *, notification_id, user_id):
        captured["notification_id"] = notification_id
        captured["user_id"] = user_id
        return notification

    monkeypatch.setattr(
        notification_service.notification_repo,
        "mark_read",
        mark_read,
    )

    result = await notification_service.mark_read(
        db,
        notification_id=notification.id,
        user_id=notification.user_id,
    )

    assert result is notification
    assert captured["notification_id"] == notification.id
    assert captured["user_id"] == notification.user_id


@pytest.mark.asyncio
async def test_order_ready_producer_uses_delivery_management_target(monkeypatch):
    captured = {}
    order = SimpleNamespace(
        id=uuid4(),
        order_code="ORD-READY",
        customer_name="Tran Binh",
        total_amount="65000.00",
    )

    async def notify_roles(db, roles, **kwargs):
        captured["roles"] = tuple(roles)
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        order_service.notification_service,
        "notify_roles",
        notify_roles,
    )

    await order_service._notify_order_ready_for_delivery(FakeDb(), order)

    assert captured["roles"] == (UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    assert captured["kwargs"]["notification_type"] == "order.ready_for_delivery"
    assert captured["kwargs"]["action_url"] == "delivery_manage.html"
    assert captured["kwargs"]["dedupe_key"] == f"order.ready_for_delivery:{order.id}"


@pytest.mark.asyncio
async def test_cod_discrepancy_producer_marks_critical(monkeypatch):
    captured = {}
    trip = SimpleNamespace(id=uuid4(), trip_code="TRIP-001")

    async def notify_roles(db, roles, **kwargs):
        captured["roles"] = tuple(roles)
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        delivery_service.notification_service,
        "notify_roles",
        notify_roles,
    )

    await delivery_service._notify_cod_discrepancy(
        FakeDb(),
        trip,
        expected_amount="65000.00",
        actual_amount="60000.00",
        discrepancy="-5000.00",
    )

    assert captured["roles"] == (UserRole.ADMIN, UserRole.DELIVERY_MANAGER)
    assert captured["kwargs"]["notification_type"] == "delivery.cod_discrepancy"
    assert captured["kwargs"]["severity"] == "critical"
    assert captured["kwargs"]["action_url"] == "delivery_manage.html"
    assert captured["kwargs"]["dedupe_key"] == f"delivery.cod_discrepancy:{trip.id}"
