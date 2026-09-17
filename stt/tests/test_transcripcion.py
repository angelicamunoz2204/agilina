"""Pruebas de humo del servicio de transcripción.

Corren en modo simulado: verifican el contrato HTTP que consume el worker sin
descargar el modelo ni exigir GPU.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_stt.config import obtener_configuracion
from agilina_stt.main import crear_aplicacion
from agilina_stt.modelo import obtener_transcriptor


@pytest.fixture(autouse=True)
def modo_simulado(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGILINA_STT_SIMULADO", "true")
    obtener_configuracion.cache_clear()
    obtener_transcriptor.cache_clear()
    yield
    obtener_configuracion.cache_clear()
    obtener_transcriptor.cache_clear()


@pytest.fixture
async def cliente() -> AsyncClient:
    transporte = ASGITransport(app=crear_aplicacion())
    async with AsyncClient(transport=transporte, base_url="http://pruebas") as cliente:
        yield cliente


async def test_la_sonda_de_estado_responde(cliente: AsyncClient):
    respuesta = await cliente.get("/salud")

    assert respuesta.status_code == 200
    assert respuesta.json()["modo"] == "simulado"


async def test_transcribir_devuelve_texto_e_idioma(cliente: AsyncClient):
    respuesta = await cliente.post(
        "/v1/transcribir",
        files={"audio": ("segmento.wav", b"RIFF....WAVE", "audio/wav")},
        data={"idioma": "en"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["idioma"] == "en"
    assert cuerpo["texto"]
    assert cuerpo["simulada"] is True
    assert cuerpo["duracion_ms"] >= 0


async def test_el_idioma_por_defecto_es_espanol(cliente: AsyncClient):
    respuesta = await cliente.post(
        "/v1/transcribir",
        files={"audio": ("segmento.wav", b"RIFF....WAVE", "audio/wav")},
    )

    assert respuesta.json()["idioma"] == "es"
