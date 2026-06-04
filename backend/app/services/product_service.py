from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.image_crypto import ImageCryptoError, decrypt_image, encrypt_image
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
    RecipeItemCreate,
    RecipeItemRead,
)
from app.services.errors import ServiceError


@dataclass(frozen=True)
class ProductImageData:
    content: bytes
    content_type: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
    category: str | None = None,
) -> Sequence[Product]:
    return await product_repo.list_products(
        db,
        is_available=is_available,
        category=category,
    )


async def list_products_by_category(
    db: AsyncSession,
    *,
    category: str | None = None,
) -> Sequence[Product]:
    return await product_repo.list_products(
        db,
        category=category,
        sort_by_category=True,
    )


async def get_product(db: AsyncSession, product_id: UUID) -> Product:
    product = await product_repo.get_product(db, product_id)
    if product is None:
        raise ServiceError("product_not_found", status_code=404)
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    if payload.selling_price <= Decimal("0"):
        raise ServiceError("product_price_must_be_positive")

    if payload.recipe is not None:
        await _validate_recipe_items(db, payload.recipe)

    try:
        category = await _get_or_create_category_by_name(db, payload.category)
        product = await product_repo.create_product(
            db,
            category_id=category.id,
            name=payload.name,
            description=payload.description,
            selling_price=payload.selling_price,
            is_available=payload.is_available,
        )
        if payload.recipe is not None:
            await product_repo.replace_product_recipe_rows(
                db,
                product.id,
                [item.model_dump() for item in payload.recipe],
            )
        await db.commit()
        product = await product_repo.get_product(db, product.id)
        if product is None:
            raise ServiceError("product_not_found", status_code=404)
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

    category_name = values.pop("category", None)
    if category_name is not None:
        category = await _get_or_create_category_by_name(db, category_name)
        values["category_id"] = category.id

    try:
        product = await product_repo.update_product(db, product, **values)
        await db.commit()
        product = await product_repo.get_product(db, product.id)
        if product is None:
            raise ServiceError("product_not_found", status_code=404)
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


async def upload_product_image(
    db: AsyncSession,
    product_id: UUID,
    *,
    content: bytes,
    content_type: str | None,
) -> Product:
    product = await get_product(db, product_id)
    normalized_content_type = _validate_image_upload(content, content_type)

    try:
        ciphertext = encrypt_image(content)
        product = await product_repo.update_product_image(
            db,
            product,
            image=ciphertext,
            image_content_type=normalized_content_type,
            image_size_bytes=len(content),
            image_updated_at=utc_now(),
        )
        await db.commit()
        product = await product_repo.get_product(db, product.id)
        if product is None:
            raise ServiceError("product_not_found", status_code=404)
        return product
    except ImageCryptoError as error:
        await db.rollback()
        raise ServiceError(str(error), status_code=500) from error
    except Exception:
        await db.rollback()
        raise


async def get_product_image(
    db: AsyncSession,
    product_id: UUID,
) -> ProductImageData:
    product = await product_repo.get_product(db, product_id)
    if product is None:
        raise ServiceError("product_not_found", status_code=404)
    if product.image is None or product.image_content_type is None:
        raise ServiceError("product_image_not_found", status_code=404)

    try:
        return ProductImageData(
            content=decrypt_image(product.image),
            content_type=product.image_content_type,
        )
    except ImageCryptoError as error:
        raise ServiceError(
            "product_image_decryption_failed", status_code=500
        ) from error


async def delete_product_image(
    db: AsyncSession,
    product_id: UUID,
) -> Product:
    product = await get_product(db, product_id)

    try:
        product = await product_repo.clear_product_image(
            db,
            product,
            image_updated_at=utc_now(),
        )
        await db.commit()
        product = await product_repo.get_product(db, product.id)
        if product is None:
            raise ServiceError("product_not_found", status_code=404)
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


def _validate_image_upload(content: bytes, content_type: str | None) -> str:
    settings = get_settings()
    allowed_content_types = {
        item.strip()
        for item in settings.product_image_allowed_content_types.split(",")
        if item.strip()
    }
    if content_type is None or content_type not in allowed_content_types:
        raise ServiceError(
            "unsupported_product_image_content_type",
            context={"allowed_content_types": sorted(allowed_content_types)},
        )
    if not content:
        raise ServiceError("product_image_empty")
    if len(content) > settings.product_image_max_size_bytes:
        raise ServiceError(
            "product_image_too_large",
            context={"max_size_bytes": settings.product_image_max_size_bytes},
        )

    return content_type


async def _get_or_create_category_by_name(
    db: AsyncSession,
    name: str,
) -> ProductCategory:
    category = await product_repo.get_category_by_name(db, name)
    if category is not None:
        return category

    return await product_repo.create_category(db, name=name)


async def _validate_recipe_items(
    db: AsyncSession,
    items: Sequence[RecipeItemCreate],
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
