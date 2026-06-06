from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.schemas.dashboard import DashboardProductRead
from app.services import dashboard_service
from app.services.errors import ServiceError


class FakeDb:
    pass


@pytest.fixture(autouse=True)
def fixed_shop_timezone(monkeypatch):
    monkeypatch.setattr(
        dashboard_service,
        "_shop_timezone",
        lambda: ZoneInfo("Asia/Ho_Chi_Minh"),
    )


def make_product():
    return SimpleNamespace(
        id=uuid4(),
        name="Matcha Latte",
        selling_price=Decimal("55000.00"),
    )


@pytest.mark.asyncio
async def test_today_dashboard_uses_shop_timezone_window(monkeypatch):
    db = FakeDb()
    captured = {}

    monkeypatch.setattr(
        dashboard_service,
        "utc_now",
        lambda: datetime(2026, 6, 6, 18, 30, tzinfo=timezone.utc),
    )

    async def sum_revenue_by_created_window(db, **kwargs):
        captured["revenue_window"] = kwargs
        return Decimal("120000.00")

    async def count_orders_by_created_window(db, **kwargs):
        captured["order_window"] = kwargs
        return 3

    async def count_completed_orders_by_completed_window(db, **kwargs):
        captured["completed_window"] = kwargs
        return 2

    async def count_delivery_queue_orders(db):
        return 4

    async def count_low_stock_ingredients(db):
        return 5

    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "sum_revenue_by_created_window",
        sum_revenue_by_created_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_orders_by_created_window",
        count_orders_by_created_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_completed_orders_by_completed_window",
        count_completed_orders_by_completed_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_delivery_queue_orders",
        count_delivery_queue_orders,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_low_stock_ingredients",
        count_low_stock_ingredients,
    )

    result = await dashboard_service.get_today_dashboard(db)

    expected_start = datetime(2026, 6, 6, 17, tzinfo=timezone.utc)
    expected_end = datetime(2026, 6, 7, 17, tzinfo=timezone.utc)
    assert result.date.isoformat() == "2026-06-07"
    assert result.revenue == Decimal("120000.00")
    assert result.order_count == 3
    assert result.completed_order_count == 2
    assert result.delivery_queue_count == 4
    assert result.low_stock_count == 5
    assert captured["revenue_window"] == {
        "window_start": expected_start,
        "window_end": expected_end,
    }
    assert captured["order_window"] == captured["revenue_window"]
    assert captured["completed_window"] == captured["revenue_window"]


@pytest.mark.asyncio
async def test_today_dashboard_defaults_empty_aggregates_to_zero(monkeypatch):
    db = FakeDb()

    async def sum_revenue_by_created_window(db, **kwargs):
        return None

    async def count_orders_by_created_window(db, **kwargs):
        return 0

    async def count_completed_orders_by_completed_window(db, **kwargs):
        return 0

    async def count_delivery_queue_orders(db):
        return 0

    async def count_low_stock_ingredients(db):
        return 0

    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "sum_revenue_by_created_window",
        sum_revenue_by_created_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_orders_by_created_window",
        count_orders_by_created_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_completed_orders_by_completed_window",
        count_completed_orders_by_completed_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_delivery_queue_orders",
        count_delivery_queue_orders,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_low_stock_ingredients",
        count_low_stock_ingredients,
    )

    result = await dashboard_service.get_today_dashboard(db)

    assert result.revenue == Decimal("0.00")
    assert result.order_count == 0
    assert result.completed_order_count == 0
    assert result.delivery_queue_count == 0
    assert result.low_stock_count == 0


@pytest.mark.asyncio
async def test_best_selling_products_use_month_window_and_product_shape(monkeypatch):
    db = FakeDb()
    captured = {}
    product = make_product()

    async def list_best_selling_products(db, **kwargs):
        captured.update(kwargs)
        return [(product, 7, Decimal("385000.00"))]

    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "list_best_selling_products",
        list_best_selling_products,
    )

    result = await dashboard_service.list_best_selling_products(db, month="2026-06")

    assert captured["window_start"] == datetime(2026, 5, 31, 17, tzinfo=timezone.utc)
    assert captured["window_end"] == datetime(2026, 6, 30, 17, tzinfo=timezone.utc)
    assert result[0].product == DashboardProductRead.model_validate(product)
    assert result[0].quantity_sold == 7
    assert result[0].revenue == Decimal("385000.00")


@pytest.mark.asyncio
async def test_best_selling_products_reject_invalid_month():
    with pytest.raises(ServiceError) as error:
        await dashboard_service.list_best_selling_products(FakeDb(), month="2026-13")

    assert error.value.code == "month_must_use_yyyy_mm_format"


@pytest.mark.asyncio
async def test_delivery_performance_quantizes_average_and_cod(monkeypatch):
    db = FakeDb()
    captured = {}

    async def count_trips_by_created_window(db, **kwargs):
        captured["total"] = kwargs
        return 5

    async def count_completed_trips_by_completed_window(db, **kwargs):
        captured["completed"] = kwargs
        return 3

    async def get_average_delivery_minutes(db, **kwargs):
        captured["average"] = kwargs
        return Decimal("42.126")

    async def sum_pending_cod_by_completed_window(db, **kwargs):
        captured["cod"] = kwargs
        return Decimal("65000")

    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_trips_by_created_window",
        count_trips_by_created_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "count_completed_trips_by_completed_window",
        count_completed_trips_by_completed_window,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "get_average_delivery_minutes",
        get_average_delivery_minutes,
    )
    monkeypatch.setattr(
        dashboard_service.dashboard_repo,
        "sum_pending_cod_by_completed_window",
        sum_pending_cod_by_completed_window,
    )

    result = await dashboard_service.get_delivery_performance(db, month="2026-06")

    expected_window = {
        "window_start": datetime(2026, 5, 31, 17, tzinfo=timezone.utc),
        "window_end": datetime(2026, 6, 30, 17, tzinfo=timezone.utc),
    }
    assert result.total_trips == 5
    assert result.completed_trips == 3
    assert result.average_delivery_minutes == Decimal("42.13")
    assert result.cod_pending == Decimal("65000.00")
    assert captured["total"] == expected_window
    assert captured["completed"] == expected_window
    assert captured["average"] == expected_window
    assert captured["cod"] == expected_window
