from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredients import Ingredient
from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
    InventoryPurchase,
    ProductRecipe,
)
from app.models.product import Product


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_ingredients(
    db: AsyncSession,
    *,
    include_deleted: bool = False,
) -> Sequence[Ingredient]:
    stmt = select(Ingredient).order_by(Ingredient.name)
    if not include_deleted:
        stmt = stmt.where(Ingredient.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    *,
    include_deleted: bool = False,
) -> Ingredient | None:
    stmt = select(Ingredient).where(Ingredient.id == ingredient_id)
    if not include_deleted:
        stmt = stmt.where(Ingredient.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_ingredient(
    db: AsyncSession,
    *,
    name: str,
    unit: str,
    cost_per_unit: Decimal,
    current_stock: Decimal = Decimal("0"),
    minimum_threshold: Decimal = Decimal("0"),
    image_url: str | None = None,
) -> Ingredient:
    ingredient = Ingredient(
        name=name,
        unit=unit,
        current_stock=current_stock,
        cost_per_unit=cost_per_unit,
        minimum_threshold=minimum_threshold,
        image_url=image_url,
    )
    db.add(ingredient)
    await db.flush()
    await db.refresh(ingredient)
    return ingredient


async def update_ingredient(
    db: AsyncSession,
    ingredient: Ingredient,
    **values: object,
) -> Ingredient:
    for field, value in values.items():
        setattr(ingredient, field, value)
    ingredient.updated_at = utc_now()

    await db.flush()
    await db.refresh(ingredient)
    return ingredient


async def soft_delete_ingredient(
    db: AsyncSession,
    ingredient: Ingredient,
) -> Ingredient:
    now = utc_now()
    ingredient.deleted_at = now
    ingredient.updated_at = now

    await db.flush()
    await db.refresh(ingredient)
    return ingredient


async def ingredient_is_referenced_by_active_recipes(
    db: AsyncSession,
    ingredient_id: UUID,
) -> bool:
    stmt = select(
        exists().where(
            ProductRecipe.ingredient_id == ingredient_id,
            ProductRecipe.product_id == Product.id,
            Product.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())


async def list_purchases(
    db: AsyncSession,
    *,
    ingredient_id: UUID | None = None,
) -> Sequence[InventoryPurchase]:
    stmt = select(InventoryPurchase).order_by(InventoryPurchase.purchased_at.desc())
    if ingredient_id is not None:
        stmt = stmt.where(InventoryPurchase.ingredient_id == ingredient_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_purchase(
    db: AsyncSession,
    *,
    ingredient_id: UUID,
    quantity: Decimal,
    cost_per_unit: Decimal,
    total_cost: Decimal,
    purchased_at: datetime,
    created_by: UUID,
    supplier_name: str | None = None,
    notes: str | None = None,
) -> InventoryPurchase:
    purchase = InventoryPurchase(
        ingredient_id=ingredient_id,
        quantity=quantity,
        cost_per_unit=cost_per_unit,
        total_cost=total_cost,
        supplier_name=supplier_name,
        notes=notes,
        purchased_at=purchased_at,
        created_by=created_by,
    )
    db.add(purchase)
    await db.flush()
    await db.refresh(purchase)
    return purchase


async def list_movements(
    db: AsyncSession,
    *,
    ingredient_id: UUID | None = None,
    movement_type: InventoryMovementType | None = None,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
) -> Sequence[InventoryMovement]:
    stmt = select(InventoryMovement).order_by(InventoryMovement.created_at.desc())
    if ingredient_id is not None:
        stmt = stmt.where(InventoryMovement.ingredient_id == ingredient_id)
    if movement_type is not None:
        stmt = stmt.where(InventoryMovement.movement_type == movement_type)
    if reference_type is not None:
        stmt = stmt.where(InventoryMovement.reference_type == reference_type)
    if reference_id is not None:
        stmt = stmt.where(InventoryMovement.reference_id == reference_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_movement(
    db: AsyncSession,
    *,
    ingredient_id: UUID,
    movement_type: InventoryMovementType,
    quantity_change: Decimal,
    stock_before: Decimal,
    stock_after: Decimal,
    unit_cost: Decimal | None = None,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
    created_by: UUID | None = None,
) -> InventoryMovement:
    movement = InventoryMovement(
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        quantity_change=quantity_change,
        stock_before=stock_before,
        stock_after=stock_after,
        unit_cost=unit_cost,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )
    db.add(movement)
    await db.flush()
    await db.refresh(movement)
    return movement


async def list_low_stock_ingredients(db: AsyncSession) -> Sequence[Ingredient]:
    stmt = (
        select(Ingredient)
        .where(
            Ingredient.deleted_at.is_(None),
            Ingredient.current_stock <= Ingredient.minimum_threshold,
        )
        .order_by(Ingredient.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def lock_ingredients_by_ids(
    db: AsyncSession,
    ingredient_ids: Sequence[UUID],
) -> Sequence[Ingredient]:
    ids = list(dict.fromkeys(ingredient_ids))
    if not ids:
        return []

    stmt = (
        select(Ingredient)
        .where(
            Ingredient.id.in_(ids),
            Ingredient.deleted_at.is_(None),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    ingredients_by_id = {
        ingredient.id: ingredient for ingredient in result.scalars().all()
    }
    return [
        ingredients_by_id[ingredient_id]
        for ingredient_id in ids
        if ingredient_id in ingredients_by_id
    ]
