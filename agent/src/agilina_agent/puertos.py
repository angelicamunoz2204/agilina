"""Puertos del worker.

La lógica de facilitación no conoce ningún SDK: habla con estos protocolos y
cada adaptador es el único lugar del código que sabe de un proveedor. Cambiar
de transcripción o de síntesis es sustituir un adaptador, no tocar la máquina
de facilitación.
"""

from typing import Protocol, runtime_checkable

from agilina_shared.contrato import ContextoCeremonia, ResultadoCeremonia
from agilina_shared.enums import Idioma


@runtime_checkable
class PuertoTranscripcion(Protocol):
    """Convierte segmentos de audio en texto. No identifica hablantes: la
    identidad llega con la pista de audio."""

    async def transcribir(self, audio: bytes, idioma: Idioma) -> str: ...

    async def disponible(self) -> bool:
        """Si responde que no, la ceremonia continúa en modo degradado."""
        ...


@runtime_checkable
class PuertoSintesis(Protocol):
    """Convierte el texto de una plantilla en audio para publicarlo en la sala."""

    async def sintetizar(self, texto: str, idioma: Idioma) -> bytes: ...


@runtime_checkable
class PuertoAPI(Protocol):
    """Las dos únicas operaciones del worker contra la API."""

    async def obtener_contexto(self, ceremonia_id: str) -> ContextoCeremonia: ...

    async def entregar_resultado(self, resultado: ResultadoCeremonia) -> None: ...
