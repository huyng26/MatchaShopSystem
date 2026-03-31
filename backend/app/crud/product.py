from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductIngredient
from app.schemas.product import ProductCreate, ProductUpdate


async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Product]:
    result = await db.execute(
        select(Product).options(selectinload(Product.ingredients)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(
        select(Product).options(selectinload(Product.ingredients)).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product_data = data.model_dump(exclude={"ingredients"})
    product = Product(**product_data)
    db.add(product)
    await db.flush()

    for ing in data.ingredients:
        pi = ProductIngredient(product_id=product.id, **ing.model_dump())
        db.add(pi)

    await db.commit()
    await db.refresh(product)
    return product


async def update_product(db: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    update_data = data.model_dump(exclude_unset=True, exclude={"ingredients"})
    for field, value in update_data.items():
        setattr(product, field, value)

    if data.ingredients is not None:
        # Replace recipe
        await db.execute(
            ProductIngredient.__table__.delete().where(ProductIngredient.product_id == product.id)
        )
        for ing in data.ingredients:
            pi = ProductIngredient(product_id=product.id, **ing.model_dump())
            db.add(pi)

    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.commit()
