from datetime import datetime, timezone

import pytest

from app.repositories import dashboard_repo


class FakeResult:
    def all(self):
        return []

    def scalar_one(self):
        return 0


class CapturingDb:
    def __init__(self) -> None:
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return FakeResult()


@pytest.mark.asyncio
async def test_best_selling_query_counts_completed_orders_by_completed_at():
    db = CapturingDb()

    await dashboard_repo.list_best_selling_products(
        db,
        window_start=datetime(2026, 5, 31, 17, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 30, 17, tzinfo=timezone.utc),
    )

    sql = str(db.statements[0])
    assert "orders.status" in sql
    assert "orders.completed_at" in sql
    assert "orders.created_at" not in sql
    assert "sum(order_items.quantity)" in sql
    assert "sum(order_items.line_total)" in sql


@pytest.mark.asyncio
async def test_average_delivery_query_requires_started_and_completed_trips():
    db = CapturingDb()

    await dashboard_repo.get_average_delivery_minutes(
        db,
        window_start=datetime(2026, 5, 31, 17, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 30, 17, tzinfo=timezone.utc),
    )

    sql = str(db.statements[0])
    assert "delivery_trips.started_at IS NOT NULL" in sql
    assert "delivery_trips.completed_at IS NOT NULL" in sql
    assert "delivery_trips.completed_at" in sql
