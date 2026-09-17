"""Carga del modelo de transcripción.

La carga es perezosa y el modo simulado no importa ``faster_whisper`` en
absoluto: así el servicio arranca en cualquier máquina y el modelo solo se
descarga donde de verdad hay GPU.
"""

from dataclasses import dataclass
from functools import lru_cache

from agilina_shared.enums import Idioma
from agilina_stt.config import obtener_configuracion

TEXTO_SIMULADO = {
    Idioma.ES: "Ayer avancé en la historia, hoy sigo con ella y no tengo bloqueos.",
    Idioma.EN: "Yesterday I worked on the story, today I continue with it, no blockers.",
}


@dataclass(frozen=True)
class Transcripcion:
    texto: str
    idioma: Idioma
    simulada: bool


class Transcriptor:
    """Puerto interno del servicio: una implementación real y una simulada."""

    def transcribir(self, audio: bytes, idioma: Idioma) -> Transcripcion:
        raise NotImplementedError


class TranscriptorSimulado(Transcriptor):
    def transcribir(self, audio: bytes, idioma: Idioma) -> Transcripcion:
        return Transcripcion(
            texto=TEXTO_SIMULADO[idioma],
            idioma=idioma,
            simulada=True,
        )


class TranscriptorWhisper(Transcriptor):
    """faster-whisper sobre GPU. Se instala con el extra ``gpu``."""

    def __init__(self, modelo: str, dispositivo: str, tipo_computo: str) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:  # pragma: sin cobertura
            raise RuntimeError(
                "faster-whisper no está instalado. Instálalo con "
                "`uv sync --package agilina-stt --extra gpu` "
                "o deja AGILINA_STT_SIMULADO=true para trabajar sin GPU."
            ) from error

        self._modelo = WhisperModel(modelo, device=dispositivo, compute_type=tipo_computo)

    def transcribir(self, audio: bytes, idioma: Idioma) -> Transcripcion:  # pragma: sin cobertura
        import io

        segmentos, _ = self._modelo.transcribe(io.BytesIO(audio), language=idioma.value)
        texto = " ".join(segmento.text.strip() for segmento in segmentos).strip()
        return Transcripcion(texto=texto, idioma=idioma, simulada=False)


@lru_cache
def obtener_transcriptor() -> Transcriptor:
    configuracion = obtener_configuracion()
    if configuracion.simulado:
        return TranscriptorSimulado()
    return TranscriptorWhisper(
        modelo=configuracion.modelo,
        dispositivo=configuracion.dispositivo,
        tipo_computo=configuracion.tipo_computo,
    )
