from collections.abc import Iterable
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ingredient import Ingredient
from app.models.order import OrderItem
from app.models.product import Product, ProductCategory, ProductRecipe


async def list_categories(db: AsyncSession) -> list[ProductCategory]:
    result = await db.execute(
        select(ProductCategory)
        .where(ProductCategory.deleted_at.is_(None))
        .order_by(ProductCategory.name)
    )
    return list(result.scalars().all())


async def get_category(db: AsyncSession, category_id: uuid.UUID) -> ProductCategory | None:
    result = await db.execute(
        select(ProductCategory).where(
            ProductCategory.id == category_id, ProductCategory.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def category_has_active_products(db: AsyncSession, category_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(func.count(Product.id)).where(
            Product.category_id == category_id, Product.deleted_at.is_(None)
        )
    )
    return bool(result.scalar_one())


async def list_products(
    db: AsyncSession, skip: int = 0, limit: int = 100, available_only: bool = False
) -> list[Product]:
    query = (
        select(Product)
        .options(selectinload(Product.recipes))
        .where(Product.deleted_at.is_(None))
        .order_by(Product.name)
    )
    if available_only:
        query = query.where(Product.is_available.is_(True))
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.recipes))
        .where(Product.id == product_id, Product.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_products(db: AsyncSession, product_ids: Iterable[uuid.UUID]) -> list[Product]:
    result = await db.execute(
        select(Product).where(Product.id.in_(product_ids), Product.deleted_at.is_(None))
    )
    return list(result.scalars().all())


async def get_ingredients(db: AsyncSession, ingredient_ids: Iterable[uuid.UUID]) -> list[Ingredient]:
    result = await db.execute(
        select(Ingredient).where(Ingredient.id.in_(ingredient_ids), Ingredient.deleted_at.is_(None))
    )
    return list(result.scalars().all())


async def product_has_order_items(db: AsyncSession, product_id: uuid.UUID) -> bool:
    result = await db.execute(select(func.count(OrderItem.id)).where(OrderItem.product_id == product_id))
    return bool(result.scalar_one())


async def ingredient_has_active_recipes(db: AsyncSession, ingredient_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(func.count(ProductRecipe.id))
        .join(Product)
        .where(ProductRecipe.ingredient_id == ingredient_id, Product.deleted_at.is_(None))
    )
    return bool(result.scalar_one())


async def list_recipes_for_products(
    db: AsyncSession, product_ids: Iterable[uuid.UUID]
) -> list[ProductRecipe]:
    result = await db.execute(select(ProductRecipe).where(ProductRecipe.product_id.in_(product_ids)))
    return list(result.scalars().all())
