from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import (
    created,
    ok,
    raise_service_error,
    read_list,
    read_one,
    require_actor_user_id,
)
from app.core.database import get_db
from app.schemas.inventory import (
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
    InventoryPurchaseCreate,
    InventoryPurchaseRead,
    LowStockIngredientRead,
)
from app.services import inventory_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("")
async def list_ingredients(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    ingredients = await inventory_service.list_ingredients(db)
    return ok(read_list(IngredientRead, ingredients))


@router.post("")
async def create_ingredient(
    payload: IngredientCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.create_ingredient(db, payload)
        return created(read_one(IngredientRead, ingredient))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/low-stock")
async def list_low_stock_ingredients(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ingredients = await inventory_service.list_low_stock_ingredients(db)
    return ok(read_list(LowStockIngredientRead, ingredients))


@router.get("/{ingredient_id}")
async def get_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.get_ingredient(db, ingredient_id)
        return ok(read_one(IngredientRead, ingredient))
    except ServiceError as error:
        raise_service_error(error)


@router.put("/{ingredient_id}")
async def update_ingredient(
    ingredient_id: UUID,
    payload: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.update_ingredient(
            db,
            ingredient_id,
            payload,
        )
        return ok(read_one(IngredientRead, ingredient), message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.delete("/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.delete_ingredient(db, ingredient_id)
        return ok(read_one(IngredientRead, ingredient), message="Deleted successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.post("/{ingredient_id}/purchases")
async def record_ingredient_purchase(
    ingredient_id: UUID,
    payload: InventoryPurchaseCreate,
    db: AsyncSession = Depends(get_db),
    actor_user_id: UUID = Depends(require_actor_user_id),
) -> dict[str, Any]:
    try:
        purchase = await inventory_service.record_ingredient_purchase(
            db,
            ingredient_id,
            payload,
            created_by=actor_user_id,
        )
        return created(read_one(InventoryPurchaseRead, purchase))
    except ServiceError as error:
        raise_service_error(error)
