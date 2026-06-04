from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ingredients import Ingredient
from app.models.inventory import ProductRecipe
from app.models.order import OrderItem
from app.models.product import Product, ProductCategory


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_categories(
    db: AsyncSession,
    *,
    include_deleted: bool = False,
) -> Sequence[ProductCategory]:
    stmt = select(ProductCategory).order_by(ProductCategory.name)
    if not include_deleted:
        stmt = stmt.where(ProductCategory.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_category(
    db: AsyncSession,
    category_id: UUID,
    *,
    include_deleted: bool = False,
) -> ProductCategory | None:
    stmt = select(ProductCategory).where(ProductCategory.id == category_id)
    if not include_deleted:
        stmt = stmt.where(ProductCategory.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_category_by_name(
    db: AsyncSession,
    name: str,
    *,
    include_deleted: bool = False,
) -> ProductCategory | None:
    stmt = select(ProductCategory).where(ProductCategory.name == name)
    if not include_deleted:
        stmt = stmt.where(ProductCategory.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_category(
    db: AsyncSession,
    *,
    name: str,
    description: str | None = None,
) -> ProductCategory:
    category = ProductCategory(name=name, description=description)
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


async def update_category(
    db: AsyncSession,
    category: ProductCategory,
    **values: object,
) -> ProductCategory:
    for field, value in values.items():
        setattr(category, field, value)
    category.updated_at = utc_now()

    await db.flush()
    await db.refresh(category)
    return category


async def soft_delete_category(
    db: AsyncSession,
    category: ProductCategory,
) -> ProductCategory:
    now = utc_now()
    category.deleted_at = now
    category.updated_at = now

    await db.flush()
    await db.refresh(category)
    return category


async def category_exists(db: AsyncSession, category_id: UUID) -> bool:
    stmt = select(
        exists().where(
            ProductCategory.id == category_id,
            ProductCategory.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())


async def list_products(
    db: AsyncSession,
    *,
    is_available: bool | None = None,
    category_id: UUID | None = None,
    category: str | None = None,
    include_deleted: bool = False,
    load_category: bool = True,
    sort_by_category: bool = False,
) -> Sequence[Product]:
    stmt = select(Product)
    if not include_deleted:
        stmt = stmt.where(Product.deleted_at.is_(None))
    if is_available is not None:
        stmt = stmt.where(Product.is_available.is_(is_available))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if category is not None:
        stmt = stmt.join(ProductCategory).where(
            ProductCategory.name == category,
            ProductCategory.deleted_at.is_(None),
        )
    if load_category:
        stmt = stmt.options(selectinload(Product.category))
    if sort_by_category:
        if category is None:
            stmt = stmt.join(ProductCategory)
        stmt = stmt.order_by(ProductCategory.name, Product.name)
    else:
        stmt = stmt.order_by(Product.name)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_product(
    db: AsyncSession,
    product_id: UUID,
    *,
    include_deleted: bool = False,
    load_category: bool = True,
) -> Product | None:
    stmt = select(Product).where(Product.id == product_id)
    if not include_deleted:
        stmt = stmt.where(Product.deleted_at.is_(None))
    if load_category:
        stmt = stmt.options(selectinload(Product.category))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession,
    *,
    category_id: UUID,
    name: str,
    selling_price: Decimal,
    description: str | None = None,
    is_available: bool = True,
) -> Product:
    product = Product(
        category_id=category_id,
        name=name,
        description=description,
        selling_price=selling_price,
        is_available=is_available,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession,
    product: Product,
    **values: object,
) -> Product:
    for field, value in values.items():
        setattr(product, field, value)
    product.updated_at = utc_now()

    await db.flush()
    await db.refresh(product)
    return product


async def update_product_image(
    db: AsyncSession,
    product: Product,
    *,
    image: bytes,
    image_content_type: str,
    image_size_bytes: int,
    image_updated_at: datetime,
) -> Product:
    product.image = image
    product.image_content_type = image_content_type
    product.image_size_bytes = image_size_bytes
    product.image_updated_at = image_updated_at
    product.updated_at = image_updated_at

    await db.flush()
    await db.refresh(product)
    return product


async def clear_product_image(
    db: AsyncSession,
    product: Product,
    *,
    image_updated_at: datetime,
) -> Product:
    product.image = None
    product.image_content_type = None
    product.image_size_bytes = None
    product.image_updated_at = image_updated_at
    product.updated_at = image_updated_at

    await db.flush()
    await db.refresh(product)
    return product


async def soft_delete_product(db: AsyncSession, product: Product) -> Product:
    now = utc_now()
    product.deleted_at = now
    product.updated_at = now

    await db.flush()
    await db.refresh(product)
    return product


async def product_exists(db: AsyncSession, product_id: UUID) -> bool:
    stmt = select(
        exists().where(
            Product.id == product_id,
            Product.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())


async def product_is_referenced_by_order_items(
    db: AsyncSession,
    product_id: UUID,
) -> bool:
    stmt = select(exists().where(OrderItem.product_id == product_id))
    result = await db.execute(stmt)
    return bool(result.scalar())


async def list_product_recipe_rows(
    db: AsyncSession,
    product_id: UUID,
    *,
    load_ingredients: bool = False,
) -> Sequence[ProductRecipe]:
    stmt = (
        select(ProductRecipe)
        .where(ProductRecipe.product_id == product_id)
        .order_by(ProductRecipe.created_at)
    )
    if load_ingredients:
        stmt = stmt.options(selectinload(ProductRecipe.ingredient))

    result = await db.execute(stmt)
    return result.scalars().all()


async def replace_product_recipe_rows(
    db: AsyncSession,
    product_id: UUID,
    recipe_items: Iterable[dict[str, UUID | Decimal]],
) -> Sequence[ProductRecipe]:
    await db.execute(
        delete(ProductRecipe).where(ProductRecipe.product_id == product_id)
    )

    rows = [
        ProductRecipe(
            product_id=product_id,
            ingredient_id=item["ingredient_id"],
            quantity_per_serving=item["quantity_per_serving"],
        )
        for item in recipe_items
    ]
    db.add_all(rows)
    await db.flush()

    return await list_product_recipe_rows(db, product_id, load_ingredients=True)


async def list_existing_recipe_ingredient_ids(
    db: AsyncSession,
    ingredient_ids: Iterable[UUID],
) -> set[UUID]:
    ids = set(ingredient_ids)
    if not ids:
        return set()

    stmt = select(Ingredient.id).where(
        Ingredient.id.in_(ids),
        Ingredient.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return set(result.scalars().all())
