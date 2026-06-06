from collections.abc import Sequence
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.ingredients import Ingredient
from app.repositories import dashboard_repo
from app.schemas.dashboard import (
    BestSellingProductRead,
    DashboardProductRead,
    DashboardTodayRead,
    DeliveryPerformanceRead,
)
from app.services.finance_service import parse_month

MONEY_QUANT = Decimal("0.01")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_today_dashboard(db: AsyncSession) -> DashboardTodayRead:
    today, window_start, window_end = _today_window()
    revenue = await dashboard_repo.sum_revenue_by_created_window(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    order_count = await dashboard_repo.count_orders_by_created_window(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    completed_order_count = (
        await dashboard_repo.count_completed_orders_by_completed_window(
            db,
            window_start=window_start,
            window_end=window_end,
        )
    )
    delivery_queue_count = await dashboard_repo.count_delivery_queue_orders(db)
    low_stock_count = await dashboard_repo.count_low_stock_ingredients(db)
    return DashboardTodayRead(
        date=today,
        revenue=_money(revenue),
        order_count=order_count,
        completed_order_count=completed_order_count,
        delivery_queue_count=delivery_queue_count,
        low_stock_count=low_stock_count,
    )


async def list_low_stock_ingredients(db: AsyncSession) -> Sequence[Ingredient]:
    return await dashboard_repo.list_low_stock_ingredients(db)


async def list_best_selling_products(
    db: AsyncSession,
    *,
    month: str,
) -> list[BestSellingProductRead]:
    window_start, window_end = _month_window(month)
    rows = await dashboard_repo.list_best_selling_products(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    return [
        BestSellingProductRead(
            product=DashboardProductRead.model_validate(product),
            quantity_sold=quantity_sold,
            revenue=_money(revenue),
        )
        for product, quantity_sold, revenue in rows
    ]


async def get_delivery_performance(
    db: AsyncSession,
    *,
    month: str,
) -> DeliveryPerformanceRead:
    window_start, window_end = _month_window(month)
    total_trips = await dashboard_repo.count_trips_by_created_window(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    completed_trips = await dashboard_repo.count_completed_trips_by_completed_window(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    average_delivery_minutes = await dashboard_repo.get_average_delivery_minutes(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    cod_pending = await dashboard_repo.sum_pending_cod_by_completed_window(
        db,
        window_start=window_start,
        window_end=window_end,
    )
    return DeliveryPerformanceRead(
        total_trips=total_trips,
        completed_trips=completed_trips,
        average_delivery_minutes=_decimal(average_delivery_minutes).quantize(
            MONEY_QUANT
        ),
        cod_pending=_money(cod_pending),
    )


def _today_window() -> tuple[date, datetime, datetime]:
    shop_timezone = _shop_timezone()
    local_today = utc_now().astimezone(shop_timezone).date()
    local_start = datetime.combine(local_today, time.min, tzinfo=shop_timezone)
    local_end = local_start + timedelta(days=1)
    return (
        local_today,
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc),
    )


def _month_window(month: str) -> tuple[datetime, datetime]:
    month_start, next_month_start = parse_month(month)
    shop_timezone = _shop_timezone()
    local_start = datetime.combine(month_start, time.min, tzinfo=shop_timezone)
    local_end = datetime.combine(next_month_start, time.min, tzinfo=shop_timezone)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _shop_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().shop_timezone)


def _money(value: Decimal | int | float | None) -> Decimal:
    return _decimal(value).quantize(MONEY_QUANT)


def _decimal(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))
