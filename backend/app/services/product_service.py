from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole
from app.models.inventory import ProductRecipe
from app.models.product import Product
from app.repositories import product_repo
from app.schemas.product import (
    ProductAvailabilityUpdate,
    ProductCreate,
    ProductRecipeRead,
    ProductRecipeUpdate,
    ProductUpdate,
    RecipeItemRead,
)
from app.services.errors import ServiceError
from app.services import notification_service


async def list_products(
    db: AsyncSession,
    *,
    is_available: bool | None = None,
    category: str | None = None,
    sort_by_category: bool = False,
) -> Sequence[Product]:
    return await product_repo.list_products(
        db,
        is_available=is_available,
        category=_normalize_category(category),
        sort_by_category=sort_by_category,
    )


async def get_product(db: AsyncSession, product_id: UUID) -> Product:
    product = await product_repo.get_product(db, product_id)
    if product is None:
        raise ServiceError("product_not_found", status_code=404)
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    if payload.selling_price <= Decimal("0"):
        raise ServiceError("product_price_must_be_positive")

    try:
        values = payload.model_dump(exclude={"recipe"})
        values["category"] = _require_category(values.get("category"))
        product = await product_repo.create_product(db, **values)

        if payload.recipe is not None:
            await _validate_recipe_items(db, payload.recipe.items)
            await product_repo.replace_product_recipe_rows(
                db,
                product.id,
                [item.model_dump() for item in payload.recipe.items],
            )

        await _notify_product_created(db, product)
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

    if "category" in values:
        values["category"] = _require_category(values.get("category"))

    try:
        product = await product_repo.update_product(db, product, **values)
        if values:
            await _notify_product_updated(db, product, values)
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
        await _notify_product_availability_changed(db, product)
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

    await _validate_recipe_items(db, payload.items)

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


async def _validate_recipe_items(
    db: AsyncSession,
    items: Sequence[Any],
) -> None:
    ingredient_ids = [item.ingredient_id for item in items]
    if len(set(ingredient_ids)) != len(ingredient_ids):
        raise ServiceError("duplicate_recipe_ingredient")

    for item in items:
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


def _build_product_recipe_read(
    product_id: UUID,
    rows: Sequence[ProductRecipe],
) -> ProductRecipeRead:
    return ProductRecipeRead(
        product_id=product_id,
        items=[RecipeItemRead.model_validate(row) for row in rows],
    )


def _normalize_category(category: str | None) -> str | None:
    if category is None:
        return None
    normalized = category.strip()
    return normalized or None


def _require_category(category: object) -> str:
    if not isinstance(category, str):
        raise ServiceError("product_category_required")

    normalized = category.strip()
    if not normalized:
        raise ServiceError("product_category_required")

    return normalized


async def _notify_product_created(db: AsyncSession, product: Product) -> None:
    await notification_service.notify_roles(
        db,
        (UserRole.ADMIN, UserRole.CASHIER),
        notification_type="product.created",
        title="New menu item",
        message=f"{product.name} has been added to the menu.",
        entity_type="product",
        entity_id=product.id,
        action_url="POS_menu.html",
        metadata={
            "product_name": product.name,
            "category": product.category,
            "selling_price": str(product.selling_price),
            "is_available": product.is_available,
        },
        dedupe_key=f"product.created:{product.id}",
    )


async def _notify_product_updated(
    db: AsyncSession,
    product: Product,
    changed_values: dict[str, object],
) -> None:
    await notification_service.notify_roles(
        db,
        (UserRole.CASHIER,),
        notification_type="product.updated",
        title="Menu item updated",
        message=f"{product.name} has been updated on the menu.",
        entity_type="product",
        entity_id=product.id,
        action_url="POS_menu.html",
        metadata={
            "product_name": product.name,
            "category": product.category,
            "changed_fields": sorted(changed_values),
            "selling_price": str(product.selling_price),
            "is_available": product.is_available,
        },
        dedupe_key=(
            f"product.updated:{product.id}:{product.updated_at.isoformat()}"
        ),
    )


async def _notify_product_availability_changed(
    db: AsyncSession,
    product: Product,
) -> None:
    status = "available" if product.is_available else "unavailable"
    await notification_service.notify_roles(
        db,
        (UserRole.CASHIER,),
        notification_type="product.availability_updated",
        title="Menu availability updated",
        message=f"{product.name} is now {status}.",
        entity_type="product",
        entity_id=product.id,
        action_url="POS_menu.html",
        metadata={
            "product_name": product.name,
            "category": product.category,
            "is_available": product.is_available,
        },
        dedupe_key=(
            f"product.availability_updated:{product.id}:"
            f"{product.is_available}:{product.updated_at.isoformat()}"
        ),
    )
