from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    product_image_encryption_key: str = "griLWrQWk4knSGGNhmlmvt9EDT-Vh7pv_7hdsRvQY-M="
    product_image_max_size_bytes: int = 2_097_152
    product_image_allowed_content_types: str = "image/jpeg,image/png,image/webp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
