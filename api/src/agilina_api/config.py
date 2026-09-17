"""Configuración de la API.

Todo se lee de variables de entorno: el repositorio no guarda ningún valor
real, solo el archivo de ejemplo con las claves esperadas (Avance 1, 7.1).
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from agilina_shared.enums import Idioma

RAIZ_REPO = Path(__file__).resolve().parents[3]


class Configuracion(BaseSettings):
    """Valores de entorno de la API.

    Las claves con prefijo ``AGILINA_`` son del producto; las de Postgres
    conservan su nombre estándar porque las comparten los contenedores.
    """

    model_config = SettingsConfigDict(
        env_file=(RAIZ_REPO / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_",
        extra="ignore",
    )

    # ------------------------------------------------------------- entorno --
    entorno: Literal["local", "nube"] = "local"
    nivel_log: str = "INFO"
    idioma_por_defecto: Idioma = Idioma.ES

    # ----------------------------------------------------------------- api --
    api_host: str = "127.0.0.1"
    api_puerto: int = 8000
    api_url_publica: str = "http://localhost:8000"
    origenes_permitidos: str = "http://localhost:4200"

    # ------------------------------------------------------------ postgres --
    url_bd: str | None = None
    postgres_usuario: str = Field(default="agilina", validation_alias="POSTGRES_USUARIO")
    postgres_clave: str = Field(default="agilina", validation_alias="POSTGRES_CLAVE")
    postgres_bd: str = Field(default="agilina", validation_alias="POSTGRES_BD")
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_puerto: int = Field(default=5432, validation_alias="POSTGRES_PUERTO")

    # ------------------------------------------------------------ keycloak --
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agilina"
    keycloak_cliente_web: str = "agilina-web"
    keycloak_cliente_worker: str = "agilina-worker"
    keycloak_secreto_worker: str = ""

    # ------------------------------------------------------------- livekit --
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # ------------------------------------------------ servicios de modelos --
    stt_url: str = "http://localhost:8001"
    gemini_api_key: str = ""
    gemini_modelo: str = "gemini-2.0-flash"
    elevenlabs_api_key: str = ""

    @property
    def dsn(self) -> str:
        """URL de conexión a Postgres.

        ``psycopg`` sirve para los dos usos del proyecto con la misma cadena:
        asíncrono para la API y síncrono para Alembic y el almacén del
        planificador.
        """
        if self.url_bd:
            return self.url_bd
        return (
            f"postgresql+psycopg://{self.postgres_usuario}:{self.postgres_clave}"
            f"@{self.postgres_host}:{self.postgres_puerto}/{self.postgres_bd}"
        )

    @property
    def origenes(self) -> list[str]:
        return [origen.strip() for origen in self.origenes_permitidos.split(",") if origen.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Configuración cacheada: se lee una vez por proceso."""
    return Configuracion()
