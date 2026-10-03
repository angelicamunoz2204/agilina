"""API settings.

Everything is read from environment variables: the repository stores no real
value, only the example file with the expected keys (Avance 1, 7.1).
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agilina_shared.enums import Language

REPO_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    """Environment values of the API.

    Keys prefixed with ``AGILINA_`` belong to the product; the Postgres ones
    keep their standard name because the containers share them.
    """

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_",
        extra="ignore",
    )

    # --------------------------------------------------------- environment --
    environment: Literal["local", "cloud"] = "local"
    log_level: str = "INFO"
    default_language: Language = Language.ES

    # ----------------------------------------------------------------- api --
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_public_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:4200"

    # ------------------------------------------------------------ postgres --
    db_url: str | None = None
    postgres_user: str = Field(default="agilina", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="agilina", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="agilina", validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")

    # ------------------------------------------------------------ keycloak --
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agilina"
    keycloak_web_client: str = "agilina-web"
    keycloak_worker_client: str = "agilina-worker"
    keycloak_worker_secret: str = ""

    # ------------------------------------------------------------- livekit --
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # ------------------------------------------------------ model services --
    stt_url: str = "http://localhost:8001"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    elevenlabs_api_key: str = ""

    @property
    def dsn(self) -> str:
        """Postgres connection URL.

        ``psycopg`` serves both uses of the project with the same string:
        asynchronous for the API and synchronous for Alembic and the scheduler
        store.
        """
        if self.db_url:
            return self.db_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings: read once per process."""
    return Settings()
