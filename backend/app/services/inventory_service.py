from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient, InventoryMovement, InventoryMovementType, InventoryPurchase
from app.repositories import inventory as inventory_repo
from app.repositories import product as product_repo
from app.schemas.inventory import IngredientCreate, IngredientUpdate, InventoryPurchaseCreate
from app.services.errors import DomainError


async def list_ingredients(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Ingredient]:
    return await inventory_repo.list_ingredients(db, skip=skip, limit=limit)


async def get_ingredient(db: AsyncSession, ingredient_id: uuid.UUID) -> Ingredient:
    ingredient = await inventory_repo.get_ingredient(db, ingredient_id)
    if ingredient is None:
        raise DomainError("Ingredient not found", 404)
    return ingredient


async def create_ingredient(db: AsyncSession, data: IngredientCreate) -> Ingredient:
    async with db.begin():
        ingredient = Ingredient(**data.model_dump())
        db.add(ingredient)
    return ingredient


async def update_ingredient(
    db: AsyncSession, ingredient_id: uuid.UUID, data: IngredientUpdate
) -> Ingredient:
    async with db.begin():
        ingredient = await inventory_repo.get_ingredient_for_update(db, ingredient_id)
        if ingredient is None:
            raise DomainError("Ingredient not found", 404)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ingredient, field, value)
    return ingredient


async def delete_ingredient(db: AsyncSession, ingredient_id: uuid.UUID) -> None:
    async with db.begin():
        ingredient = await inventory_repo.get_ingredient_for_update(db, ingredient_id)
        if ingredient is None:
            raise DomainError("Ingredient not found", 404)
        if await product_repo.ingredient_has_active_recipes(db, ingredient_id):
            raise DomainError("Ingredient is used by an active product recipe")
        ingredient.deleted_at = datetime.now(timezone.utc)


async def record_purchase(
    db: AsyncSession,
    ingredient_id: uuid.UUID,
    data: InventoryPurchaseCreate,
    actor_user_id: uuid.UUID,
) -> InventoryPurchase:
    async with db.begin():
        ingredient = await inventory_repo.get_ingredient_for_update(db, ingredient_id)
        if ingredient is None:
            raise DomainError("Ingredient not found", 404)

        stock_before = Decimal(ingredient.current_stock)
        stock_after = stock_before + data.quantity
        purchase = InventoryPurchase(
            ingredient_id=ingredient.id,
            quantity=data.quantity,
            cost_per_unit=data.cost_per_unit,
            total_cost=data.quantity * data.cost_per_unit,
            supplier_name=data.supplier_name,
            notes=data.notes,
            created_by=actor_user_id,
        )
        db.add(purchase)
        await db.flush()
        db.add(
            InventoryMovement(
                ingredient_id=ingredient.id,
                movement_type=InventoryMovementType.purchase,
                quantity_change=data.quantity,
                stock_before=stock_before,
                stock_after=stock_after,
                unit_cost=data.cost_per_unit,
                reference_type="inventory_purchase",
                reference_id=purchase.id,
                created_by=actor_user_id,
            )
        )
        ingredient.current_stock = stock_after
    return purchase


async def list_purchases(
    db: AsyncSession, ingredient_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> list[InventoryPurchase]:
    return await inventory_repo.list_purchases(db, ingredient_id, skip, limit)


async def list_movements(
    db: AsyncSession, ingredient_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> list[InventoryMovement]:
    return await inventory_repo.list_movements(db, ingredient_id, skip, limit)


async def get_low_stock_ingredients(db: AsyncSession) -> list[Ingredient]:
    return await inventory_repo.list_low_stock_ingredients(db)
