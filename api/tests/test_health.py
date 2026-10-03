"""Smoke test: the API starts and responds."""

from httpx import AsyncClient


async def test_the_liveness_probe_responds(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "agilina-api"
    assert body["status"] == "alive"
    assert body["version"]


async def test_the_readiness_probe_reports_when_there_is_no_database(client: AsyncClient):
    """Without Postgres up the API stays alive but declares itself not ready."""
    response = await client.get("/health/ready")

    assert response.status_code in (200, 503)
    body = response.json()
    if response.status_code == 503:
        assert body["database"] == "unavailable"
    else:
        assert body["database"] == "available"
