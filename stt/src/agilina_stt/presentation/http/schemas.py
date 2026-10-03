"""HTTP request and response models of the transcription service."""

from pydantic import BaseModel

from agilina_shared.enums import Language


class ServiceStatus(BaseModel):
    service: str = "agilina-stt"
    version: str
    status: str
    mode: str
    model: str
    device: str


class TranscriptionResponse(BaseModel):
    text: str
    language: Language
    simulated: bool
    duration_ms: int
