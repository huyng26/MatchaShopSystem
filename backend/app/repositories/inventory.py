from collections.abc import Iterable
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient, InventoryMovement, InventoryPurchase


async def list_ingredients(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Ingredient]:
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.deleted_at.is_(None))
        .order_by(Ingredient.name)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_low_stock_ingredients(db: AsyncSession) -> list[Ingredient]:
    result = await db.execute(
        select(Ingredient)
        .where(
            Ingredient.deleted_at.is_(None),
            Ingredient.current_stock <= Ingredient.minimum_threshold,
        )
        .order_by(Ingredient.name)
    )
    return list(result.scalars().all())


async def get_ingredient(db: AsyncSession, ingredient_id: uuid.UUID) -> Ingredient | None:
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ingredient_id, Ingredient.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_ingredient_for_update(db: AsyncSession, ingredient_id: uuid.UUID) -> Ingredient | None:
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.id == ingredient_id, Ingredient.deleted_at.is_(None))
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def get_ingredients_for_update(
    db: AsyncSession, ingredient_ids: Iterable[uuid.UUID]
) -> list[Ingredient]:
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.id.in_(ingredient_ids), Ingredient.deleted_at.is_(None))
        .with_for_update()
    )
    return list(result.scalars().all())


async def list_purchases(
    db: AsyncSession, ingredient_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> list[InventoryPurchase]:
    query = select(InventoryPurchase)
    if ingredient_id is not None:
        query = query.where(InventoryPurchase.ingredient_id == ingredient_id)
    result = await db.execute(
        query.order_by(InventoryPurchase.purchased_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def list_movements(
    db: AsyncSession, ingredient_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100
) -> list[InventoryMovement]:
    query = select(InventoryMovement)
    if ingredient_id is not None:
        query = query.where(InventoryMovement.ingredient_id == ingredient_id)
    result = await db.execute(
        query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())
