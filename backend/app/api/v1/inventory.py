from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import ok, read_list
from app.core.database import get_db
from app.models.inventory import InventoryMovementType
from app.schemas.inventory import (
    InventoryMovementRead,
    InventoryPurchaseRead,
    LowStockIngredientRead,
)
from app.services import inventory_service

router = APIRouter()


@router.get("/purchases")
async def list_purchases(
    ingredient_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    purchases = await inventory_service.list_purchases(
        db,
        ingredient_id=ingredient_id,
    )
    return ok(read_list(InventoryPurchaseRead, purchases))


@router.get("/movements")
async def list_movements(
    ingredient_id: UUID | None = Query(default=None),
    movement_type: InventoryMovementType | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    reference_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    movements = await inventory_service.list_movements(
        db,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    return ok(read_list(InventoryMovementRead, movements))


@router.get("/low-stock")
async def list_low_stock_ingredients(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ingredients = await inventory_service.list_low_stock_ingredients(db)
    return ok(read_list(LowStockIngredientRead, ingredients))
