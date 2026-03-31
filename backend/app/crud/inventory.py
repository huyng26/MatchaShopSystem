from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient, IngredientPurchase
from app.schemas.inventory import IngredientCreate, IngredientUpdate, IngredientPurchaseCreate


async def get_ingredients(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Ingredient]:
    result = await db.execute(select(Ingredient).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_ingredient(db: AsyncSession, ingredient_id: int) -> Ingredient | None:
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    return result.scalar_one_or_none()


async def create_ingredient(db: AsyncSession, data: IngredientCreate) -> Ingredient:
    ingredient = Ingredient(**data.model_dump())
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


async def update_ingredient(db: AsyncSession, ingredient: Ingredient, data: IngredientUpdate) -> Ingredient:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ingredient, field, value)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


async def delete_ingredient(db: AsyncSession, ingredient: Ingredient) -> None:
    await db.delete(ingredient)
    await db.commit()


async def adjust_stock(db: AsyncSession, ingredient: Ingredient, delta: Decimal) -> Ingredient:
    """Add or subtract stock quantity."""
    ingredient.current_stock = Decimal(str(ingredient.current_stock)) + delta
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


# --- Purchases ---

async def create_purchase(db: AsyncSession, data: IngredientPurchaseCreate) -> IngredientPurchase:
    total_cost = data.quantity * data.unit_cost
    purchase = IngredientPurchase(**data.model_dump(), total_cost=total_cost)
    db.add(purchase)

    ingredient = await get_ingredient(db, data.ingredient_id)
    if ingredient:
        await adjust_stock(db, ingredient, data.quantity)

    await db.commit()
    await db.refresh(purchase)
    return purchase


async def get_purchases(
    db: AsyncSession, ingredient_id: int | None = None, skip: int = 0, limit: int = 100
) -> list[IngredientPurchase]:
    query = select(IngredientPurchase)
    if ingredient_id is not None:
        query = query.where(IngredientPurchase.ingredient_id == ingredient_id)
    query = query.order_by(IngredientPurchase.purchased_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
