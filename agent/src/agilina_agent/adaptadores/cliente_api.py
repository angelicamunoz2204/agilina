"""Adaptador del worker contra la API de Agilina.

Se autentica con la cuenta de servicio del worker en Keycloak (credenciales de
cliente) y reintenta si la API no responde: perder el resultado de una
ceremonia por un reinicio de la API no es aceptable.
"""

import asyncio
from collections.abc import Callable

import httpx

from agilina_agent.puertos import PuertoAPI
from agilina_agent.registro import obtener_registro
from agilina_shared.contrato import ContextoCeremonia, ResultadoCeremonia

registro = obtener_registro(__name__)

REINTENTOS = 3
ESPERA_ENTRE_REINTENTOS = 2.0


class ClienteAPI(PuertoAPI):
    def __init__(
        self,
        url_base: str,
        obtener_token: Callable[[], str] | None = None,
        cliente: httpx.AsyncClient | None = None,
    ) -> None:
        self._url_base = url_base.rstrip("/")
        self._obtener_token = obtener_token
        self._cliente = cliente or httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))

    def _cabeceras(self) -> dict[str, str]:
        if self._obtener_token is None:
            return {}
        return {"Authorization": f"Bearer {self._obtener_token()}"}

    async def obtener_contexto(self, ceremonia_id: str) -> ContextoCeremonia:
        respuesta = await self._cliente.get(
            f"{self._url_base}/v1/ceremonias/{ceremonia_id}/contexto",
            headers=self._cabeceras(),
        )
        respuesta.raise_for_status()
        return ContextoCeremonia.model_validate(respuesta.json())

    async def entregar_resultado(self, resultado: ResultadoCeremonia) -> None:
        ultimo_error: Exception | None = None

        for intento in range(1, REINTENTOS + 1):
            try:
                respuesta = await self._cliente.post(
                    f"{self._url_base}/v1/ceremonias/{resultado.ceremonia_id}/resultado",
                    content=resultado.model_dump_json(),
                    headers={"Content-Type": "application/json", **self._cabeceras()},
                )
                respuesta.raise_for_status()
            except httpx.HTTPStatusError as error:
                # Un 4xx es un resultado que la API rechaza: reintentarlo no lo
                # arregla. Solo se reintenta lo que puede ser transitorio.
                if error.response.status_code < 500:
                    raise
                ultimo_error = error
            except httpx.TransportError as error:
                ultimo_error = error
            else:
                registro.info("Resultado de la ceremonia %s entregado", resultado.ceremonia_id)
                return

            registro.warning(
                "Intento %s de %s al entregar el resultado falló: %s",
                intento,
                REINTENTOS,
                ultimo_error,
            )
            if intento < REINTENTOS:
                await asyncio.sleep(ESPERA_ENTRE_REINTENTOS * intento)

        raise RuntimeError("No fue posible entregar el resultado a la API") from ultimo_error

    async def cerrar(self) -> None:
        await self._cliente.aclose()
