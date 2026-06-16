from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import SHOP_LATITUDE, SHOP_LONGITUDE


class Settings(BaseSettings):
    app_name: str = "Matcha Shop Backend"
    app_env: str = "development"
    debug: bool = True

    database_url: str = (
        "postgresql+asyncpg://admin:password@db:5432/matcha_management_system"
    )
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    shop_timezone: str = "Asia/Ho_Chi_Minh"
    shop_latitude: float = SHOP_LATITUDE
    shop_longitude: float = SHOP_LONGITUDE
    google_maps_api_key: str | None = None
    openrouteservice_api_key: str | None = None
    maps_provider: str = "openrouteservice"
    maps_request_timeout_seconds: float = 8.0
    shipper_location_update_interval_seconds: int = 30
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_product_images_bucket: str = "product-images"
    product_image_max_size_bytes: int = 2 * 1024 * 1024

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> Any:
        release_values = {"release", "prod", "production"}
        if isinstance(value, str) and value.lower() in release_values:
            return False
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
