from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import ok, raise_service_error, read_list
from app.core.constants import UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.models.user import User
from app.schemas.dashboard import (
    BestSellingProductRead,
    DashboardTodayRead,
    DeliveryPerformanceRead,
)
from app.schemas.inventory import LowStockIngredientRead
from app.services import dashboard_service
from app.services.errors import ServiceError

router = APIRouter()

DashboardUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)),
]


@router.get("/today")
async def get_today_dashboard(
    _current_user: DashboardUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    today = await dashboard_service.get_today_dashboard(db)
    return ok(DashboardTodayRead.model_validate(today))


@router.get("/low-stock")
async def get_low_stock_dashboard(
    _current_user: DashboardUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    ingredients = await dashboard_service.list_low_stock_ingredients(db)
    return ok(read_list(LowStockIngredientRead, ingredients))


@router.get("/best-selling-products")
async def get_best_selling_products(
    _current_user: DashboardUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str,
) -> dict[str, Any]:
    try:
        products = await dashboard_service.list_best_selling_products(db, month=month)
        return ok(
            [BestSellingProductRead.model_validate(product) for product in products]
        )
    except ServiceError as error:
        raise_service_error(error)


@router.get("/delivery-performance")
async def get_delivery_performance(
    _current_user: DashboardUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: str,
) -> dict[str, Any]:
    try:
        performance = await dashboard_service.get_delivery_performance(
            db,
            month=month,
        )
        return ok(DeliveryPerformanceRead.model_validate(performance))
    except ServiceError as error:
        raise_service_error(error)
