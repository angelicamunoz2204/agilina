"""Adaptador de síntesis de voz.

La implementación real llega con la historia que le da voz a Agilina; el
adaptador simulado existe desde ahora para poder ejecutar la ceremonia
completa en local sin gastar minutos de un servicio de pago.
"""

from agilina_agent.puertos import PuertoSintesis
from agilina_agent.registro import obtener_registro
from agilina_shared.enums import Idioma

registro = obtener_registro(__name__)


class AdaptadorElevenLabs(PuertoSintesis):
    def __init__(self, api_key: str, voz_por_idioma: dict[Idioma, str]) -> None:
        self._api_key = api_key
        self._voz_por_idioma = voz_por_idioma

    async def sintetizar(self, texto: str, idioma: Idioma) -> bytes:
        raise NotImplementedError(
            "Síntesis de voz pendiente: HU-15. El puerto y el adaptador simulado "
            "ya permiten ejercitar la máquina de facilitación."
        )


class SintesisSimulada(PuertoSintesis):
    """Registra lo que Agilina diría en vez de sintetizarlo.

    Es lo que permite correr una ceremonia de punta a punta en local, y también
    lo que usan las pruebas.
    """

    def __init__(self) -> None:
        self.dicho: list[tuple[Idioma, str]] = []

    async def sintetizar(self, texto: str, idioma: Idioma) -> bytes:
        self.dicho.append((idioma, texto))
        registro.info("[voz simulada · %s] %s", idioma.value, texto)
        return b""
