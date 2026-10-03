"""Worker settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from agilina_shared.enums import Language

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    default_language: Language = Language.ES

    # LiveKit: the worker generates its own token with room permissions.
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # The API is the only source of context and the only destination of the result.
    api_public_url: str = "http://localhost:8000"

    # Keycloak service account the worker authenticates with.
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agilina"
    keycloak_worker_client: str = "agilina-worker"
    keycloak_worker_secret: str = ""

    # Transcription service, never exposed to the internet.
    stt_url: str = "http://localhost:8001"

    # Speech synthesis.
    elevenlabs_api_key: str = ""
    elevenlabs_voice_es: str = ""
    elevenlabs_voice_en: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
