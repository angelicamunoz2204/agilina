"""Transcription service settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_STT_",
        extra="ignore",
    )

    model: str = "small"
    device: Literal["cpu", "cuda"] = "cpu"
    compute_type: str = "int8"
    simulated: bool = True
    """In simulated mode the service answers without loading the model.

    It is what lets the whole chain run on a machine without a GPU and what
    keeps the pipeline under ten minutes: downloading the model on every CI run
    would add nothing the test does not verify anyway.
    """


@lru_cache
def get_settings() -> Settings:
    return Settings()
