import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi import Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

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
from app.services.storage_service import UploadedProductImage
from app.services.storage_service import delete_product_image, upload_product_image

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
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    uploaded_image: UploadedProductImage | None = None
    product_created = False
    try:
        payload, image_file = await _parse_product_create_request(request)
        if image_file is not None:
            uploaded_image = await upload_product_image(image_file)
            payload = payload.model_copy(update={"image_url": uploaded_image.public_url})

        product = await product_service.create_product(db, payload)
        product_created = True
        return created(read_one(ProductRead, product))
    except ServiceError as error:
        if not product_created:
            await _cleanup_uploaded_product_image(uploaded_image)
        raise_service_error(error)
    except ValidationError as error:
        if not product_created:
            await _cleanup_uploaded_product_image(uploaded_image)
        raise RequestValidationError(error.errors()) from error
    except Exception:
        if not product_created:
            await _cleanup_uploaded_product_image(uploaded_image)
        raise


@router.get("/category")
async def list_products_by_category(
    is_available: bool | None = Query(default=None),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    products = await product_service.list_products(
        db,
        is_available=is_available,
        category=category,
        sort_by_category=True,
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
async def create_or_replace_product_recipe(
    product_id: UUID,
    payload: ProductRecipeUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        recipe = await product_service.replace_product_recipe(db, product_id, payload)
        return ok(recipe, message="Updated successfully")
    except ServiceError as error:
        raise_service_error(error)


async def _parse_product_create_request(
    request: Request,
) -> tuple[ProductCreate, UploadFile | None]:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        return await _parse_multipart_product_create_request(request)

    return ProductCreate.model_validate(await request.json()), None


async def _parse_multipart_product_create_request(
    request: Request,
) -> tuple[ProductCreate, UploadFile | None]:
    form = await request.form()
    image_file = _get_upload_file(form.get("image")) or _get_upload_file(
        form.get("file")
    )

    values: dict[str, Any] = {}
    for field in (
        "category",
        "name",
        "description",
        "selling_price",
        "is_available",
        "image_url",
    ):
        value = form.get(field)
        if value is None or isinstance(value, StarletteUploadFile):
            continue
        values[field] = (
            None if field in {"description", "image_url"} and value == "" else value
        )

    recipe = form.get("recipe")
    if recipe is not None and not isinstance(recipe, StarletteUploadFile):
        try:
            values["recipe"] = json.loads(recipe) if recipe else None
        except json.JSONDecodeError as error:
            raise ServiceError("invalid_product_recipe_json") from error

    return ProductCreate.model_validate(values), image_file


def _get_upload_file(value: Any) -> UploadFile | None:
    if isinstance(value, StarletteUploadFile) and value.filename:
        return value
    return None


async def _cleanup_uploaded_product_image(
    uploaded_image: UploadedProductImage | None,
) -> None:
    if uploaded_image is None:
        return

    try:
        await delete_product_image(uploaded_image.object_path)
    except ServiceError:
        pass
