"""Smoke tests of the transcription service.

They run in simulated mode: they verify the HTTP contract the worker consumes
without downloading the model or requiring a GPU.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_stt.infrastructure.settings import get_settings
from agilina_stt.main import create_app


@pytest.fixture(autouse=True)
def simulated_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGILINA_STT_SIMULATED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://tests") as client:
        yield client


async def test_the_status_probe_responds(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "simulated"


async def test_transcribe_returns_text_and_language(client: AsyncClient):
    response = await client.post(
        "/v1/transcribe",
        files={"audio": ("segment.wav", b"RIFF....WAVE", "audio/wav")},
        data={"language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en"
    assert body["text"]
    assert body["simulated"] is True
    assert body["duration_ms"] >= 0


async def test_the_default_language_is_spanish(client: AsyncClient):
    response = await client.post(
        "/v1/transcribe",
        files={"audio": ("segment.wav", b"RIFF....WAVE", "audio/wav")},
    )

    assert response.json()["language"] == "es"
