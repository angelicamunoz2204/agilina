"""Transcriber implementations.

Loading is lazy and the simulated mode does not import ``faster_whisper`` at
all: that way the service starts on any machine and the model is only
downloaded where there really is a GPU.
"""

import io

from agilina_shared.enums import Language
from agilina_stt.application.ports import Transcriber
from agilina_stt.domain.transcription import Transcription
from agilina_stt.infrastructure.settings import Settings

SIMULATED_TEXT = {
    Language.ES: "Ayer avancé en la historia, hoy sigo con ella y no tengo bloqueos.",
    Language.EN: "Yesterday I worked on the story, today I continue with it, no blockers.",
}


class SimulatedTranscriber(Transcriber):
    def transcribe(self, audio: bytes, language: Language) -> Transcription:
        return Transcription(text=SIMULATED_TEXT[language], language=language, simulated=True)


class WhisperTranscriber(Transcriber):
    """faster-whisper on GPU. Installed with the ``gpu`` extra."""

    def __init__(self, model: str, device: str, compute_type: str) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:  # pragma: no cover
            raise RuntimeError(
                "faster-whisper is not installed. Install it with "
                "`uv sync --package agilina-stt --extra gpu` "
                "or leave AGILINA_STT_SIMULATED=true to work without a GPU."
            ) from error

        self._model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio: bytes, language: Language) -> Transcription:  # pragma: no cover
        segments, _ = self._model.transcribe(io.BytesIO(audio), language=language.value)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return Transcription(text=text, language=language, simulated=False)


def build_transcriber(settings: Settings) -> Transcriber:
    if settings.simulated:
        return SimulatedTranscriber()
    return WhisperTranscriber(
        model=settings.model,
        device=settings.device,
        compute_type=settings.compute_type,
    )
