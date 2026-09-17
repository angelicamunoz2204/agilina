"""Prueba de humo: la API arranca y responde."""

from httpx import AsyncClient


async def test_la_sonda_de_vida_responde(cliente: AsyncClient):
    respuesta = await cliente.get("/salud")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["servicio"] == "agilina-api"
    assert cuerpo["estado"] == "vivo"
    assert cuerpo["version"]


async def test_la_sonda_de_preparacion_avisa_cuando_no_hay_base_de_datos(cliente: AsyncClient):
    """Sin Postgres levantado la API sigue viva pero se declara no preparada."""
    respuesta = await cliente.get("/salud/preparado")

    assert respuesta.status_code in (200, 503)
    cuerpo = respuesta.json()
    if respuesta.status_code == 503:
        assert cuerpo["base_de_datos"] == "no disponible"
    else:
        assert cuerpo["base_de_datos"] == "disponible"
