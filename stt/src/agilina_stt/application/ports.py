"""Ports of the transcription service."""

from dataclasses import dataclass
from typing import Protocol

from agilina_shared.enums import Language
from agilina_stt.domain.transcription import Transcription


class Transcriber(Protocol):
    """One real implementation (faster-whisper) and one simulated."""

    def transcribe(self, audio: bytes, language: Language) -> Transcription: ...


@dataclass(frozen=True)
class ServiceInfo:
    """What the health probe reports; resolved once by the composition root."""

    version: str
    mode: str
    model: str
    device: str
