"""Application settings via Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "local", "recette", "preprod", "production"]


class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "YurPass"
    app_env: Environment = "dev"
    debug: bool = False

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: str = "postgresql+psycopg://yurpass:yurpass@localhost:5432/yurpass_dev"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    refresh_cookie_name: str = "yurpass_refresh_token"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def jwt_secret_key(self) -> str:
        """Return JWT signing secret — must be set explicitly in production."""
        if self.jwt_secret:
            return self.jwt_secret
        if self.is_production:
            msg = "JWT_SECRET must be set in production"
            raise ValueError(msg)
        return "dev-only-insecure-jwt-secret-do-not-use-in-production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
