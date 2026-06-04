from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredients import Ingredient
from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
    InventoryPurchase,
)
from app.repositories import inventory_repo
from app.schemas.inventory import (
    IngredientCreate,
    IngredientUpdate,
    InventoryPurchaseCreate,
)
from app.services.errors import ServiceError

MONEY_QUANT = Decimal("0.01")


async def list_ingredients(db: AsyncSession) -> Sequence[Ingredient]:
    return await inventory_repo.list_ingredients(db)


async def get_ingredient(db: AsyncSession, ingredient_id: UUID) -> Ingredient:
    ingredient = await inventory_repo.get_ingredient(db, ingredient_id)
    if ingredient is None:
        raise ServiceError("ingredient_not_found", status_code=404)
    return ingredient


async def create_ingredient(
    db: AsyncSession,
    payload: IngredientCreate,
) -> Ingredient:
    _validate_non_negative_inventory_values(
        current_stock=payload.current_stock,
        cost_per_unit=payload.cost_per_unit,
        minimum_threshold=payload.minimum_threshold,
    )

    try:
        ingredient = await inventory_repo.create_ingredient(db, **payload.model_dump())
        await db.commit()
        return ingredient
    except Exception:
        await db.rollback()
        raise


async def update_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    payload: IngredientUpdate,
) -> Ingredient:
    ingredient = await get_ingredient(db, ingredient_id)
    values = payload.model_dump(exclude_unset=True)
    _validate_non_negative_inventory_values(**values)

    try:
        ingredient = await inventory_repo.update_ingredient(db, ingredient, **values)
        await db.commit()
        return ingredient
    except Exception:
        await db.rollback()
        raise


async def delete_ingredient(db: AsyncSession, ingredient_id: UUID) -> Ingredient:
    ingredient = await get_ingredient(db, ingredient_id)
    if await inventory_repo.ingredient_is_referenced_by_active_recipes(
        db,
        ingredient_id,
    ):
        raise ServiceError("ingredient_used_by_recipe", status_code=409)

    try:
        ingredient = await inventory_repo.soft_delete_ingredient(db, ingredient)
        await db.commit()
        return ingredient
    except Exception:
        await db.rollback()
        raise


async def record_ingredient_purchase(
    db: AsyncSession,
    ingredient_id: UUID,
    payload: InventoryPurchaseCreate,
    *,
    created_by: UUID,
) -> InventoryPurchase:
    if payload.ingredient_id != ingredient_id:
        raise ServiceError("ingredient_id_mismatch")
    if payload.quantity <= Decimal("0"):
        raise ServiceError("purchase_quantity_must_be_positive")
    if payload.cost_per_unit < Decimal("0"):
        raise ServiceError("ingredient_cost_must_be_non_negative")

    try:
        locked = await inventory_repo.lock_ingredients_by_ids(db, [ingredient_id])
        if not locked:
            raise ServiceError("ingredient_not_found", status_code=404)

        ingredient = locked[0]
        stock_before = ingredient.current_stock
        stock_after = stock_before + payload.quantity
        total_cost = (payload.quantity * payload.cost_per_unit).quantize(MONEY_QUANT)

        ingredient.current_stock = stock_after
        ingredient.cost_per_unit = payload.cost_per_unit
        await inventory_repo.update_ingredient(db, ingredient)

        purchase = await inventory_repo.create_purchase(
            db,
            ingredient_id=ingredient_id,
            quantity=payload.quantity,
            cost_per_unit=payload.cost_per_unit,
            total_cost=total_cost,
            supplier_name=payload.supplier_name,
            notes=payload.notes,
            purchased_at=payload.purchased_at,
            created_by=created_by,
        )
        await inventory_repo.create_movement(
            db,
            ingredient_id=ingredient_id,
            movement_type=InventoryMovementType.PURCHASE,
            quantity_change=payload.quantity,
            stock_before=stock_before,
            stock_after=stock_after,
            unit_cost=payload.cost_per_unit,
            reference_type="inventory_purchase",
            reference_id=purchase.id,
            created_by=created_by,
        )
        await db.commit()
        return purchase
    except Exception:
        await db.rollback()
        raise


async def list_purchases(
    db: AsyncSession,
    *,
    ingredient_id: UUID | None = None,
) -> Sequence[InventoryPurchase]:
    return await inventory_repo.list_purchases(db, ingredient_id=ingredient_id)


async def list_movements(
    db: AsyncSession,
    *,
    ingredient_id: UUID | None = None,
    movement_type: InventoryMovementType | None = None,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
) -> Sequence[InventoryMovement]:
    return await inventory_repo.list_movements(
        db,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=reference_id,
    )


async def list_low_stock_ingredients(db: AsyncSession) -> Sequence[Ingredient]:
    return await inventory_repo.list_low_stock_ingredients(db)


def _validate_non_negative_inventory_values(**values: Decimal | object) -> None:
    for field in ("current_stock", "cost_per_unit", "minimum_threshold"):
        value = values.get(field)
        if value is not None and value < Decimal("0"):
            raise ServiceError(f"{field}_must_be_non_negative")
