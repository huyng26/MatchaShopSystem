from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import created, ok, raise_service_error, read_list, read_one
from app.core.database import get_db
from app.schemas.product import (
    ProductAvailabilityUpdate,
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
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    products = await product_service.list_products(
        db,
        is_available=is_available,
        category=category,
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


@router.get("/category")
async def list_products_by_category(
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    products = await product_service.list_products_by_category(
        db,
        category=category,
    )
    return ok(read_list(ProductRead, products))


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


@router.put("/{product_id}/image")
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        content = await file.read()
        product = await product_service.upload_product_image(
            db,
            product_id,
            content=content,
            content_type=file.content_type,
        )
        return ok(read_one(ProductRead, product), message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)
    finally:
        await file.close()


@router.get("/{product_id}/image")
async def get_product_image(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        image = await product_service.get_product_image(db, product_id)
        return Response(content=image.content, media_type=image.content_type)
    except ServiceError as error:
        raise_service_error(error)


@router.delete("/{product_id}/image")
async def delete_product_image(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        product = await product_service.delete_product_image(db, product_id)
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


@router.post("/{product_id}/recipe")
async def create_product_recipe(
    product_id: UUID,
    payload: ProductRecipeUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        recipe = await product_service.replace_product_recipe(db, product_id, payload)
        return created(recipe)
    except ServiceError as error:
        raise_service_error(error)
