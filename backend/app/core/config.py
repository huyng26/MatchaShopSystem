from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Matcha Shop Backend"
    app_env: str = "development"
    debug: bool = True

    database_url: str = (
        "postgresql+asyncpg://matcha:matcha_secret@db:5432/matcha_shop"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
