"""Adaptador del servicio de transcripción autohospedado.

Habla HTTP contra el servicio de faster-whisper por la red privada de la
instancia. El audio nunca sale de la infraestructura del equipo.
"""

import httpx

from agilina_agent.puertos import PuertoTranscripcion
from agilina_shared.enums import Idioma

TIEMPO_LIMITE = httpx.Timeout(10.0, connect=3.0)


class AdaptadorWhisper(PuertoTranscripcion):
    def __init__(self, url_base: str, cliente: httpx.AsyncClient | None = None) -> None:
        self._url_base = url_base.rstrip("/")
        self._cliente = cliente or httpx.AsyncClient(timeout=TIEMPO_LIMITE)

    async def transcribir(self, audio: bytes, idioma: Idioma) -> str:
        respuesta = await self._cliente.post(
            f"{self._url_base}/v1/transcribir",
            files={"audio": ("segmento.wav", audio, "audio/wav")},
            data={"idioma": idioma.value},
        )
        respuesta.raise_for_status()
        return respuesta.json()["texto"]

    async def disponible(self) -> bool:
        try:
            respuesta = await self._cliente.get(f"{self._url_base}/salud", timeout=3.0)
        except httpx.HTTPError:
            return False
        return respuesta.status_code == 200

    async def cerrar(self) -> None:
        await self._cliente.aclose()
