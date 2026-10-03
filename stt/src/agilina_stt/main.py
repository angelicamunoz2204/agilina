"""Transcription service entry point and composition root.

make stt   → http://localhost:8001/docs
"""

from functools import lru_cache

from fastapi import FastAPI

from agilina_stt import __version__
from agilina_stt.application.ports import ServiceInfo, Transcriber
from agilina_stt.infrastructure.settings import get_settings
from agilina_stt.infrastructure.transcribers import build_transcriber
from agilina_stt.presentation.http.dependencies import get_service_info, get_transcriber
from agilina_stt.presentation.http.router import router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Agilina STT",
        version=__version__,
        description="Audio segment transcription. Internal use of the worker.",
    )
    app.include_router(router)

    info = ServiceInfo(
        version=__version__,
        mode="simulated" if settings.simulated else "model",
        model=settings.model,
        device=settings.device,
    )

    @lru_cache(maxsize=1)
    def transcriber() -> Transcriber:
        # Lazy: the model is only loaded on the first request that needs it.
        return build_transcriber(settings)

    app.dependency_overrides[get_transcriber] = transcriber
    app.dependency_overrides[get_service_info] = lambda: info
    return app


app = create_app()
