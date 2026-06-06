from types import SimpleNamespace

import pytest

from app.services import storage_service
from app.services.errors import ServiceError


def _settings(max_size: int = 10) -> SimpleNamespace:
    return SimpleNamespace(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role-key",
        supabase_product_images_bucket="product-images",
        product_image_max_size_bytes=max_size,
    )


class UploadFileStub:
    def __init__(self, content: bytes, content_type: str) -> None:
        self._content = content
        self.content_type = content_type

    async def read(self, size: int = -1) -> bytes:
        if size < 0:
            return self._content
        return self._content[:size]


def _upload_file(content: bytes, content_type: str) -> UploadFileStub:
    return UploadFileStub(content, content_type)


@pytest.mark.asyncio
async def test_upload_product_image_rejects_unsupported_type(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings())

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_product_image(
            _upload_file(b"content", "text/plain")
        )

    assert error.value.code == "unsupported_product_image_type"


@pytest.mark.asyncio
async def test_upload_product_image_rejects_empty_file(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings())

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_product_image(_upload_file(b"", "image/png"))

    assert error.value.code == "product_image_empty"


@pytest.mark.asyncio
async def test_upload_product_image_rejects_oversized_file(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings(max_size=3))

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_product_image(_upload_file(b"1234", "image/png"))

    assert error.value.code == "product_image_too_large"


@pytest.mark.asyncio
async def test_upload_ingredient_image_rejects_unsupported_type(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings())

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_ingredient_image(
            _upload_file(b"content", "text/plain")
        )

    assert error.value.code == "unsupported_ingredient_image_type"


@pytest.mark.asyncio
async def test_upload_ingredient_image_rejects_empty_file(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings())

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_ingredient_image(_upload_file(b"", "image/png"))

    assert error.value.code == "ingredient_image_empty"


@pytest.mark.asyncio
async def test_upload_ingredient_image_rejects_oversized_file(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: _settings(max_size=3))

    with pytest.raises(ServiceError) as error:
        await storage_service.upload_ingredient_image(
            _upload_file(b"1234", "image/png")
        )

    assert error.value.code == "ingredient_image_too_large"
