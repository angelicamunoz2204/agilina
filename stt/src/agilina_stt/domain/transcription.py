"""The result of transcribing an audio segment."""

from dataclasses import dataclass

from agilina_shared.enums import Language


@dataclass(frozen=True)
class Transcription:
    text: str
    language: Language
    simulated: bool
