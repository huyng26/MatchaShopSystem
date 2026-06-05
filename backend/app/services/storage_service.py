from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import uuid4

import httpx
from fastapi import UploadFile

from app.core.config import get_settings
from app.services.errors import ServiceError


ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class UploadedProductImage:
    public_url: str
    object_path: str


async def upload_product_image(file: UploadFile) -> UploadedProductImage:
    settings = get_settings()
    _require_supabase_settings(settings.supabase_url, settings.supabase_service_role_key)

    content_type = file.content_type
    if content_type not in ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES:
        raise ServiceError(
            "unsupported_product_image_type",
            context={"allowed_content_types": sorted(ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES)},
        )

    max_size = settings.product_image_max_size_bytes
    content = await file.read(max_size + 1)
    if not content:
        raise ServiceError("product_image_empty")

    if len(content) > max_size:
        raise ServiceError(
            "product_image_too_large",
            context={"max_size_bytes": max_size},
        )

    extension = ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES[content_type]
    object_path = str(PurePosixPath("products") / f"{uuid4()}{extension}")
    base_url = _normalized_supabase_url(settings.supabase_url)
    bucket = settings.supabase_product_images_bucket
    upload_url = f"{base_url}/storage/v1/object/{bucket}/{object_path}"

    api_key = settings.supabase_service_role_key
    headers = {
        "apikey": api_key,
        "Content-Type": content_type,
        "x-upsert": "false",
    }
    if not api_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.post(upload_url, content=content, headers=headers)

    if response.status_code not in {200, 201}:
        raise ServiceError(
            "product_image_upload_failed",
            status_code=502,
            context={
                "storage_status_code": response.status_code,
                "storage_response": _storage_error_text(response),
            },
        )

    return UploadedProductImage(
        public_url=f"{base_url}/storage/v1/object/public/{bucket}/{object_path}",
        object_path=object_path,
    )


async def delete_product_image(object_path: str) -> None:
    settings = get_settings()
    _require_supabase_settings(settings.supabase_url, settings.supabase_service_role_key)

    base_url = _normalized_supabase_url(settings.supabase_url)
    bucket = settings.supabase_product_images_bucket
    delete_url = f"{base_url}/storage/v1/object/{bucket}"
    api_key = settings.supabase_service_role_key
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    if not api_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.request(
            "DELETE",
            delete_url,
            json={"prefixes": [object_path]},
            headers=headers,
        )

    if response.status_code not in {200, 204}:
        raise ServiceError(
            "product_image_delete_failed",
            status_code=502,
            context={
                "storage_status_code": response.status_code,
                "storage_response": _storage_error_text(response),
            },
        )


def _require_supabase_settings(
    supabase_url: str | None,
    service_role_key: str | None,
) -> None:
    if not supabase_url or not service_role_key:
        raise ServiceError("product_image_storage_not_configured", status_code=500)


def _normalized_supabase_url(supabase_url: str | None) -> str:
    if supabase_url is None:
        raise ServiceError("product_image_storage_not_configured", status_code=500)
    return supabase_url.rstrip("/")


def _storage_error_text(response: httpx.Response) -> str:
    return response.text[:500]
