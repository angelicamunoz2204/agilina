"""Configuración del worker."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from agilina_shared.enums import Idioma

RAIZ_REPO = Path(__file__).resolve().parents[3]


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(RAIZ_REPO / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_",
        extra="ignore",
    )

    entorno: str = "local"
    nivel_log: str = "INFO"
    idioma_por_defecto: Idioma = Idioma.ES

    # LiveKit: el worker genera su propio token con permisos de sala.
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # La API es la única fuente de contexto y el único destino del resultado.
    api_url_publica: str = "http://localhost:8000"

    # Cuenta de servicio en Keycloak con la que el worker se autentica.
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agilina"
    keycloak_cliente_worker: str = "agilina-worker"
    keycloak_secreto_worker: str = ""

    # Servicio de transcripción, nunca expuesto a internet.
    stt_url: str = "http://localhost:8001"

    # Síntesis de voz.
    elevenlabs_api_key: str = ""
    elevenlabs_voz_es: str = ""
    elevenlabs_voz_en: str = ""


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
