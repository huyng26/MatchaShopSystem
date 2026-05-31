from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.integration_contracts import write_audit
from app.models.product import Product, ProductCategory, ProductRecipe
from app.repositories import product as product_repo
from app.schemas.product import (
    ProductAvailabilityUpdate,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductRecipeItem,
    ProductUpdate,
)
from app.services.errors import DomainError


async def _validate_category(db: AsyncSession, category_id: uuid.UUID) -> None:
    if await product_repo.get_category(db, category_id) is None:
        raise DomainError("Product category not found", 404)


async def _validate_recipe_ingredients(db: AsyncSession, ingredients: list[ProductRecipeItem]) -> None:
    ingredient_ids = {item.ingredient_id for item in ingredients}
    found = {ingredient.id for ingredient in await product_repo.get_ingredients(db, ingredient_ids)}
    missing = ingredient_ids - found
    if missing:
        raise DomainError(f"Ingredients not found: {sorted(str(item) for item in missing)}", 404)


async def list_categories(db: AsyncSession) -> list[ProductCategory]:
    return await product_repo.list_categories(db)


async def create_category(db: AsyncSession, data: ProductCategoryCreate) -> ProductCategory:
    async with db.begin():
        category = ProductCategory(**data.model_dump())
        db.add(category)
    return category


async def update_category(
    db: AsyncSession, category_id: uuid.UUID, data: ProductCategoryUpdate
) -> ProductCategory:
    async with db.begin():
        category = await product_repo.get_category(db, category_id)
        if category is None:
            raise DomainError("Product category not found", 404)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
    return category


async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> None:
    async with db.begin():
        category = await product_repo.get_category(db, category_id)
        if category is None:
            raise DomainError("Product category not found", 404)
        if await product_repo.category_has_active_products(db, category_id):
            raise DomainError("Product category still contains active products")
        category.deleted_at = datetime.now(timezone.utc)


async def list_products(
    db: AsyncSession, skip: int = 0, limit: int = 100, available_only: bool = False
) -> list[Product]:
    return await product_repo.list_products(db, skip, limit, available_only)


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await product_repo.get_product(db, product_id)
    if product is None:
        raise DomainError("Product not found", 404)
    return product


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    async with db.begin():
        await _validate_category(db, data.category_id)
        await _validate_recipe_ingredients(db, data.ingredients)
        product = Product(**data.model_dump(exclude={"ingredients"}))
        db.add(product)
        await db.flush()
        db.add_all(
            [
                ProductRecipe(product_id=product.id, **ingredient.model_dump())
                for ingredient in data.ingredients
            ]
        )
        await db.flush()
        await db.refresh(product, attribute_names=["recipes"])
    return product


async def update_product(db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate) -> Product:
    async with db.begin():
        product = await product_repo.get_product(db, product_id)
        if product is None:
            raise DomainError("Product not found", 404)
        if data.category_id is not None:
            await _validate_category(db, data.category_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
    return product


async def update_availability(
    db: AsyncSession, product_id: uuid.UUID, data: ProductAvailabilityUpdate
) -> Product:
    return await update_product(db, product_id, ProductUpdate(is_available=data.is_available))


async def replace_recipe(
    db: AsyncSession, product_id: uuid.UUID, ingredients: list[ProductRecipeItem]
) -> Product:
    async with db.begin():
        product = await product_repo.get_product(db, product_id)
        if product is None:
            raise DomainError("Product not found", 404)
        await _validate_recipe_ingredients(db, ingredients)
        product.recipes.clear()
        product.recipes.extend(
            ProductRecipe(product_id=product.id, **ingredient.model_dump())
            for ingredient in ingredients
        )
        await db.flush()
        await db.refresh(product, attribute_names=["recipes"])
    return product


async def delete_product(db: AsyncSession, product_id: uuid.UUID, actor_user_id: uuid.UUID) -> None:
    async with db.begin():
        product = await product_repo.get_product(db, product_id)
        if product is None:
            raise DomainError("Product not found", 404)
        if await product_repo.product_has_order_items(db, product_id):
            raise DomainError("Product is linked to existing orders. Hide product instead.")
        product.deleted_at = datetime.now(timezone.utc)
        await write_audit(db, actor_user_id, "product.deleted", "product", product.id)
