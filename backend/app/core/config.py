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
    shop_latitude: float = 10.776889
    shop_longitude: float = 106.700806

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
