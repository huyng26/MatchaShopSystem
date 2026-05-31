import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.integration_contracts import Actor, require_roles
from app.schemas.inventory import (
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
    InventoryMovementResponse,
    InventoryPurchaseCreate,
    InventoryPurchaseResponse,
)
from app.services import inventory_service

router = APIRouter()
inventory_read = require_roles("admin", "inventory_manager")
inventory_write = require_roles("admin", "inventory_manager")


@router.get("/ingredients", response_model=list[IngredientResponse])
async def list_ingredients(
    skip: int = 0,
    limit: int = 100,
    _: Actor = Depends(inventory_read),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_ingredients(db, skip, limit)


@router.get("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: uuid.UUID,
    _: Actor = Depends(inventory_read),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.get_ingredient(db, ingredient_id)


@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    data: IngredientCreate,
    _: Actor = Depends(inventory_write),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.create_ingredient(db, data)


@router.put("/ingredients/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: uuid.UUID,
    data: IngredientUpdate,
    _: Actor = Depends(inventory_write),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.update_ingredient(db, ingredient_id, data)


@router.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: uuid.UUID,
    _: Actor = Depends(inventory_write),
    db: AsyncSession = Depends(get_db),
):
    await inventory_service.delete_ingredient(db, ingredient_id)


@router.post(
    "/ingredients/{ingredient_id}/purchases",
    response_model=InventoryPurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_purchase(
    ingredient_id: uuid.UUID,
    data: InventoryPurchaseCreate,
    actor: Actor = Depends(inventory_write),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.record_purchase(db, ingredient_id, data, actor.user_id)


@router.get("/inventory/purchases", response_model=list[InventoryPurchaseResponse])
async def list_purchases(
    ingredient_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    _: Actor = Depends(inventory_read),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_purchases(db, ingredient_id, skip, limit)


@router.get("/inventory/movements", response_model=list[InventoryMovementResponse])
async def list_movements(
    ingredient_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    _: Actor = Depends(inventory_read),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.list_movements(db, ingredient_id, skip, limit)


@router.get("/inventory/low-stock", response_model=list[IngredientResponse])
async def list_low_stock(
    _: Actor = Depends(inventory_read),
    db: AsyncSession = Depends(get_db),
):
    return await inventory_service.get_low_stock_ingredients(db)
