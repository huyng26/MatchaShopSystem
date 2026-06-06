from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.api.v1.deps import (
    created,
    ok,
    raise_service_error,
    read_list,
    read_one,
    require_actor_user_id,
)
from app.core.database import get_db
from app.schemas.inventory import (
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
    InventoryPurchaseCreate,
    InventoryPurchaseRead,
    LowStockIngredientRead,
)
from app.services import inventory_service
from app.services.errors import ServiceError
from app.services.storage_service import UploadedIngredientImage
from app.services.storage_service import (
    delete_ingredient_image,
    upload_ingredient_image,
)

router = APIRouter()


@router.get("")
async def list_ingredients(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    ingredients = await inventory_service.list_ingredients(db)
    return ok(read_list(IngredientRead, ingredients))


@router.post("")
async def create_ingredient(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    uploaded_image: UploadedIngredientImage | None = None
    ingredient_created = False
    try:
        payload, image_file = await _parse_ingredient_create_request(request)
        if image_file is not None:
            uploaded_image = await upload_ingredient_image(image_file)
            payload = payload.model_copy(update={"image_url": uploaded_image.public_url})

        ingredient = await inventory_service.create_ingredient(db, payload)
        ingredient_created = True
        return created(read_one(IngredientRead, ingredient))
    except ServiceError as error:
        if not ingredient_created:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise_service_error(error)
    except ValidationError as error:
        if not ingredient_created:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise RequestValidationError(error.errors()) from error
    except Exception:
        if not ingredient_created:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise


@router.get("/low-stock")
async def list_low_stock_ingredients(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    ingredients = await inventory_service.list_low_stock_ingredients(db)
    return ok(read_list(LowStockIngredientRead, ingredients))


@router.get("/{ingredient_id}")
async def get_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.get_ingredient(db, ingredient_id)
        return ok(read_one(IngredientRead, ingredient))
    except ServiceError as error:
        raise_service_error(error)


@router.put("/{ingredient_id}")
async def update_ingredient(
    ingredient_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    uploaded_image: UploadedIngredientImage | None = None
    ingredient_updated = False
    try:
        payload, image_file = await _parse_ingredient_update_request(request)
        if image_file is not None:
            uploaded_image = await upload_ingredient_image(image_file)
            payload = payload.model_copy(update={"image_url": uploaded_image.public_url})

        ingredient = await inventory_service.update_ingredient(
            db,
            ingredient_id,
            payload,
        )
        ingredient_updated = True
        return ok(read_one(IngredientRead, ingredient), message="Updated successfully")
    except ServiceError as error:
        if not ingredient_updated:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise_service_error(error)
    except ValidationError as error:
        if not ingredient_updated:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise RequestValidationError(error.errors()) from error
    except Exception:
        if not ingredient_updated:
            await _cleanup_uploaded_ingredient_image(uploaded_image)
        raise


@router.delete("/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        ingredient = await inventory_service.delete_ingredient(db, ingredient_id)
        return ok(read_one(IngredientRead, ingredient), message="Deleted successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.post("/{ingredient_id}/purchases")
async def record_ingredient_purchase(
    ingredient_id: UUID,
    payload: InventoryPurchaseCreate,
    db: AsyncSession = Depends(get_db),
    actor_user_id: UUID = Depends(require_actor_user_id),
) -> dict[str, Any]:
    try:
        purchase = await inventory_service.record_ingredient_purchase(
            db,
            ingredient_id,
            payload,
            created_by=actor_user_id,
        )
        return created(read_one(InventoryPurchaseRead, purchase))
    except ServiceError as error:
        raise_service_error(error)


async def _parse_ingredient_create_request(
    request: Request,
) -> tuple[IngredientCreate, UploadFile | None]:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        values, image_file = await _parse_multipart_ingredient_request(request)
        return IngredientCreate.model_validate(values), image_file

    return IngredientCreate.model_validate(await request.json()), None


async def _parse_ingredient_update_request(
    request: Request,
) -> tuple[IngredientUpdate, UploadFile | None]:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        values, image_file = await _parse_multipart_ingredient_request(request)
        return IngredientUpdate.model_validate(values), image_file

    return IngredientUpdate.model_validate(await request.json()), None


async def _parse_multipart_ingredient_request(
    request: Request,
) -> tuple[dict[str, Any], UploadFile | None]:
    form = await request.form()
    image_file = _get_upload_file(form.get("image")) or _get_upload_file(
        form.get("file")
    )

    values: dict[str, Any] = {}
    for field in (
        "name",
        "unit",
        "current_stock",
        "cost_per_unit",
        "minimum_threshold",
        "image_url",
    ):
        value = form.get(field)
        if value is None or isinstance(value, StarletteUploadFile):
            continue
        values[field] = None if field == "image_url" and value == "" else value

    return values, image_file


def _get_upload_file(value: Any) -> UploadFile | None:
    if isinstance(value, StarletteUploadFile) and value.filename:
        return value
    return None


async def _cleanup_uploaded_ingredient_image(
    uploaded_image: UploadedIngredientImage | None,
) -> None:
    if uploaded_image is None:
        return

    try:
        await delete_ingredient_image(uploaded_image.object_path)
    except ServiceError:
        pass
