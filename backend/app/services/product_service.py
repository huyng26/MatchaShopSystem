from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import ProductRecipe
from app.models.product import Product, ProductCategory
from app.repositories import product_repo
from app.schemas.product import (
    ProductAvailabilityUpdate,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductRecipeRead,
    ProductRecipeUpdate,
    ProductUpdate,
    RecipeItemRead,
)
from app.services.errors import ServiceError


async def list_categories(db: AsyncSession) -> Sequence[ProductCategory]:
    return await product_repo.list_categories(db)


async def get_category(db: AsyncSession, category_id: UUID) -> ProductCategory:
    category = await product_repo.get_category(db, category_id)
    if category is None:
        raise ServiceError("category_not_found", status_code=404)
    return category


async def create_category(
    db: AsyncSession,
    payload: ProductCategoryCreate,
) -> ProductCategory:
    try:
        category = await product_repo.create_category(db, **payload.model_dump())
        await db.commit()
        return category
    except Exception:
        await db.rollback()
        raise


async def update_category(
    db: AsyncSession,
    category_id: UUID,
    payload: ProductCategoryUpdate,
) -> ProductCategory:
    category = await get_category(db, category_id)
    values = payload.model_dump(exclude_unset=True)

    try:
        category = await product_repo.update_category(db, category, **values)
        await db.commit()
        return category
    except Exception:
        await db.rollback()
        raise


async def delete_category(db: AsyncSession, category_id: UUID) -> ProductCategory:
    category = await get_category(db, category_id)

    try:
        category = await product_repo.soft_delete_category(db, category)
        await db.commit()
        return category
    except Exception:
        await db.rollback()
        raise


async def list_products(
    db: AsyncSession,
    *,
    is_available: bool | None = None,
    category_id: UUID | None = None,
) -> Sequence[Product]:
    return await product_repo.list_products(
        db,
        is_available=is_available,
        category_id=category_id,
    )


async def get_product(db: AsyncSession, product_id: UUID) -> Product:
    product = await product_repo.get_product(db, product_id)
    if product is None:
        raise ServiceError("product_not_found", status_code=404)
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    if payload.selling_price <= Decimal("0"):
        raise ServiceError("product_price_must_be_positive")
    if not await product_repo.category_exists(db, payload.category_id):
        raise ServiceError("category_not_found", status_code=404)

    try:
        product = await product_repo.create_product(db, **payload.model_dump())
        await db.commit()
        return product
    except Exception:
        await db.rollback()
        raise


async def update_product(
    db: AsyncSession,
    product_id: UUID,
    payload: ProductUpdate,
) -> Product:
    product = await get_product(db, product_id)
    values = payload.model_dump(exclude_unset=True)

    selling_price = values.get("selling_price")
    if selling_price is not None and selling_price <= Decimal("0"):
        raise ServiceError("product_price_must_be_positive")

    category_id = values.get("category_id")
    if category_id is not None and not await product_repo.category_exists(
        db, category_id
    ):
        raise ServiceError("category_not_found", status_code=404)

    try:
        product = await product_repo.update_product(db, product, **values)
        await db.commit()
        return product
    except Exception:
        await db.rollback()
        raise


async def delete_product(db: AsyncSession, product_id: UUID) -> Product:
    product = await get_product(db, product_id)
    if await product_repo.product_is_referenced_by_order_items(db, product_id):
        raise ServiceError("product_linked_to_orders", status_code=409)

    try:
        product = await product_repo.soft_delete_product(db, product)
        await db.commit()
        return product
    except Exception:
        await db.rollback()
        raise


async def toggle_product_availability(
    db: AsyncSession,
    product_id: UUID,
    payload: ProductAvailabilityUpdate,
) -> Product:
    product = await get_product(db, product_id)

    try:
        product = await product_repo.update_product(
            db,
            product,
            is_available=payload.is_available,
        )
        await db.commit()
        return product
    except Exception:
        await db.rollback()
        raise


async def get_product_recipe(
    db: AsyncSession,
    product_id: UUID,
) -> ProductRecipeRead:
    if not await product_repo.product_exists(db, product_id):
        raise ServiceError("product_not_found", status_code=404)

    rows = await product_repo.list_product_recipe_rows(
        db,
        product_id,
        load_ingredients=True,
    )
    return _build_product_recipe_read(product_id, rows)


async def replace_product_recipe(
    db: AsyncSession,
    product_id: UUID,
    payload: ProductRecipeUpdate,
) -> ProductRecipeRead:
    if not await product_repo.product_exists(db, product_id):
        raise ServiceError("product_not_found", status_code=404)

    ingredient_ids = [item.ingredient_id for item in payload.items]
    if len(set(ingredient_ids)) != len(ingredient_ids):
        raise ServiceError("duplicate_recipe_ingredient")

    for item in payload.items:
        if item.quantity_per_serving <= Decimal("0"):
            raise ServiceError("recipe_quantity_must_be_positive")

    existing_ids = await product_repo.list_existing_recipe_ingredient_ids(
        db,
        ingredient_ids,
    )
    missing_ids = sorted(
        str(ingredient_id) for ingredient_id in set(ingredient_ids) - existing_ids
    )
    if missing_ids:
        raise ServiceError(
            "recipe_ingredient_not_found",
            status_code=404,
            context={"ingredient_ids": missing_ids},
        )

    try:
        rows = await product_repo.replace_product_recipe_rows(
            db,
            product_id,
            [item.model_dump() for item in payload.items],
        )
        await db.commit()
        return _build_product_recipe_read(product_id, rows)
    except Exception:
        await db.rollback()
        raise


def _build_product_recipe_read(
    product_id: UUID,
    rows: Sequence[ProductRecipe],
) -> ProductRecipeRead:
    return ProductRecipeRead(
        product_id=product_id,
        items=[RecipeItemRead.model_validate(row) for row in rows],
    )
