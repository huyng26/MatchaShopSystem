from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import created, ok, raise_service_error, read_list, read_one
from app.core.database import get_db
from app.schemas.product import (
    ProductAvailabilityUpdate,
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCategoryUpdate,
    ProductCreate,
    ProductRead,
    ProductRecipeUpdate,
    ProductUpdate,
)
from app.services import product_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("")
async def list_products(
    is_available: bool | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    products = await product_service.list_products(
        db,
        is_available=is_available,
        category_id=category_id,
    )
    return ok(read_list(ProductRead, products))


@router.post("")
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.create_product(db, payload)
        return created(read_one(ProductRead, product))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    categories = await product_service.list_categories(db)
    return ok(read_list(ProductCategoryRead, categories))


@router.post("/categories")
async def create_category(
    payload: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        category = await product_service.create_category(db, payload)
        return created(read_one(ProductCategoryRead, category))
    except ServiceError as error:
        raise_service_error(error)


@router.put("/categories/{category_id}")
async def update_category(
    category_id: UUID,
    payload: ProductCategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        category = await product_service.update_category(db, category_id, payload)
        return ok(
            read_one(ProductCategoryRead, category), message="Updated successfully"
        )
    except ServiceError as error:
        raise_service_error(error)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        category = await product_service.delete_category(db, category_id)
        return ok(
            read_one(ProductCategoryRead, category), message="Deleted successfully"
        )
    except ServiceError as error:
        raise_service_error(error)


@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.get_product(db, product_id)
        return ok(read_one(ProductRead, product))
    except ServiceError as error:
        raise_service_error(error)


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.update_product(db, product_id, payload)
        return ok(read_one(ProductRead, product), message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.patch("/{product_id}/availability")
async def update_product_availability(
    product_id: UUID,
    payload: ProductAvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.toggle_product_availability(
            db,
            product_id,
            payload,
        )
        return ok(read_one(ProductRead, product), message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.delete_product(db, product_id)
        return ok(read_one(ProductRead, product), message="Deleted successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.get("/{product_id}/recipe")
async def get_product_recipe(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        recipe = await product_service.get_product_recipe(db, product_id)
        return ok(recipe)
    except ServiceError as error:
        raise_service_error(error)


@router.put("/{product_id}/recipe")
async def replace_product_recipe(
    product_id: UUID,
    payload: ProductRecipeUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        recipe = await product_service.replace_product_recipe(db, product_id, payload)
        return ok(recipe, message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)
