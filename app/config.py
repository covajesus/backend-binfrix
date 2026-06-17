from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "Binfrix API"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    secret_key: str = "binfrix-dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:5176,http://127.0.0.1:5176"
    )
    api_public_url: str = "http://localhost:8000"
    ecommerce_public_url: str = "http://localhost:5174"

    database_url: str = ""

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_user: str = "binfrix"
    mysql_password: str = ""
    mysql_database: str = "binfrix"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        password = quote_plus(self.mysql_password)
        user = quote_plus(self.mysql_user)
        return (
            f"mysql+pymysql://{user}:{password}@"
            f"{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
