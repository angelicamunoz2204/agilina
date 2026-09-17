"""El contrato worker ↔ API está publicado en la especificación desde el
primer commit, aunque su implementación llegue con HU-56."""

from httpx import AsyncClient


async def test_la_especificacion_publica_las_dos_operaciones_del_worker(cliente: AsyncClient):
    especificacion = (await cliente.get("/openapi.json")).json()

    rutas = especificacion["paths"]
    assert "/v1/ceremonias/{ceremonia_id}/contexto" in rutas
    assert "/v1/ceremonias/{ceremonia_id}/resultado" in rutas


async def test_las_operaciones_declaran_que_todavia_no_estan_implementadas(cliente: AsyncClient):
    respuesta = await cliente.get("/v1/ceremonias/8f2f0d7e-0e4c-4a2e-9a0e-0b3b1a4a1c11/contexto")

    assert respuesta.status_code == 501
    assert "HU-56" in respuesta.json()["detalle"]
