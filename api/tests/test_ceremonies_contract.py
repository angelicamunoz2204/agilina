"""The worker ↔ API contract is published in the specification from the first
commit, even though its implementation arrives with HU-56."""

from httpx import AsyncClient


async def test_the_specification_publishes_the_two_worker_operations(client: AsyncClient):
    specification = (await client.get("/openapi.json")).json()

    paths = specification["paths"]
    assert "/v1/ceremonies/{ceremony_id}/context" in paths
    assert "/v1/ceremonies/{ceremony_id}/result" in paths


async def test_the_operations_declare_they_are_not_implemented_yet(client: AsyncClient):
    response = await client.get("/v1/ceremonies/8f2f0d7e-0e4c-4a2e-9a0e-0b3b1a4a1c11/context")

    assert response.status_code == 501
    assert "HU-56" in response.json()["detail"]
