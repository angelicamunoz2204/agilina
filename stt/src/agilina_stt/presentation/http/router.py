"""HTTP interface of the transcription service.

Only the worker consumes it, over the private network of the instance: this
service is never exposed to the internet.
"""

import time

from fastapi import APIRouter, Depends, Form, UploadFile

from agilina_shared.enums import Language
from agilina_stt.application.ports import ServiceInfo, Transcriber
from agilina_stt.presentation.http.dependencies import get_service_info, get_transcriber
from agilina_stt.presentation.http.schemas import ServiceStatus, TranscriptionResponse

router = APIRouter()


@router.get("/health", response_model=ServiceStatus, tags=["health"], summary="Status probe")
async def health(info: ServiceInfo = Depends(get_service_info)) -> ServiceStatus:
    return ServiceStatus(
        version=info.version,
        status="alive",
        mode=info.mode,
        model=info.model,
        device=info.device,
    )


@router.post(
    "/v1/transcribe",
    response_model=TranscriptionResponse,
    tags=["transcription"],
    summary="Transcribe an audio segment",
)
async def transcribe(
    audio: UploadFile,
    language: Language = Form(default=Language.ES),
    transcriber: Transcriber = Depends(get_transcriber),
) -> TranscriptionResponse:
    content = await audio.read()
    started = time.perf_counter()
    result = transcriber.transcribe(content, language)
    duration_ms = int((time.perf_counter() - started) * 1000)

    return TranscriptionResponse(
        text=result.text,
        language=result.language,
        simulated=result.simulated,
        duration_ms=duration_ms,
    )
