"""Configuración del servicio de transcripción."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPO = Path(__file__).resolve().parents[3]


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(RAIZ_REPO / ".env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="AGILINA_STT_",
        extra="ignore",
    )

    modelo: str = "small"
    dispositivo: Literal["cpu", "cuda"] = "cpu"
    tipo_computo: str = "int8"
    simulado: bool = True
    """En modo simulado el servicio responde sin cargar el modelo.

    Es lo que permite correr la cadena completa en una máquina sin GPU y lo que
    mantiene el pipeline por debajo de los diez minutos: descargar el modelo en
    cada ejecución de CI no aportaría nada que la prueba no verifique igual.
    """


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
