"""Adapter for the self-hosted transcription service.

It speaks HTTP to the faster-whisper service over the instance's private
network. The audio never leaves the team's infrastructure.
"""

import httpx

from agilina_agent.application.ports import Transcriber
from agilina_shared.enums import Language

TIMEOUT = httpx.Timeout(10.0, connect=3.0)


class WhisperTranscriber(Transcriber):
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=TIMEOUT)

    async def transcribe(self, audio: bytes, language: Language) -> str:
        response = await self._client.post(
            f"{self._base_url}/v1/transcribe",
            files={"audio": ("segment.wav", audio, "audio/wav")},
            data={"language": language.value},
        )
        response.raise_for_status()
        return str(response.json()["text"])

    async def is_available(self) -> bool:
        try:
            response = await self._client.get(f"{self._base_url}/health", timeout=3.0)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    async def close(self) -> None:
        await self._client.aclose()
