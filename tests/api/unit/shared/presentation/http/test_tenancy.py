"""Which tenant a request is about: required, and the same 404 for every tenant that is not
there (HU: AD-29)."""

import pytest
from httpx import AsyncClient

from agilina_api.shared.application.tenancy import TenantNotFoundError
from agilina_api.shared.presentation.http.tenancy import TENANT_HEADER, current_tenant

# A route that needs a tenant and nothing else: the invitation's status. A token that is
# not one answers 404 (not found), so the tenant is resolved before anything about the token.
URL = "/v1/invitations/status"
BODY = {"token": "x" * 43}


async def _status(client: AsyncClient, tenant: str | None) -> tuple[int, dict]:
    headers = {} if tenant is None else {TENANT_HEADER: tenant}
    response = await client.post(URL, json=BODY, headers=headers)
    return response.status_code, response.json()


async def test_a_request_without_a_tenant_is_a_400(client):
    status, body = await _status(client, None)

    assert status == 400 and body["error"]["code"] == "tenant_required"


async def test_an_empty_tenant_is_the_same_400(client):
    status, body = await _status(client, "")

    assert status == 400 and body["error"]["code"] == "tenant_required"


async def test_a_tenant_of_the_catalog_is_the_one_the_request_is_about(tenants):
    tenant = await current_tenant("ecomoda", tenants)

    assert (tenant.slug, tenant.display_name) == ("ecomoda", "Ecomoda")


async def test_the_catalog_is_asked_with_the_name_exactly_as_it_came(tenants):
    with pytest.raises(TenantNotFoundError):
        await current_tenant("ACME", tenants)

    assert tenants.asked == ["ACME"]  # no lowercasing, no trimming: that would be guessing


@pytest.mark.parametrize(
    "tenant", ["nobody", "initech", "Acme", "acme ", "acme;drop", "platform", "../acme"]
)
async def test_an_unknown_suspended_or_invalid_tenant_is_always_the_same_404(client, tenant):
    # initech is suspended; the others do not exist or are not even valid names.
    status, body = await _status(client, tenant)

    assert status == 404
    assert body["error"]["code"] == "tenant_not_found"


async def test_the_tenant_errors_are_not_cached(client):
    response = await client.post(URL, json=BODY, headers={TENANT_HEADER: "nobody"})

    assert response.headers["cache-control"] == "no-store"


# ----------------------------------------------------------------------- GET /v1/tenant --
async def test_the_web_asks_which_organization_an_address_names(client):
    response = await client.get("/v1/tenant", headers={TENANT_HEADER: "ecomoda"})

    assert response.status_code == 200
    assert response.json() == {"slug": "ecomoda", "display_name": "Ecomoda", "language": "es"}
    assert response.headers["cache-control"] == "no-store"


async def test_it_needs_no_session(client):
    response = await client.get("/v1/tenant", headers={TENANT_HEADER: "acme"})

    assert response.status_code == 200 and response.json()["language"] == "en"


async def test_it_answers_like_every_other_route_when_the_tenant_is_not_there(client):
    assert (await client.get("/v1/tenant")).status_code == 400
    for tenant in ["nobody", "initech", "Acme"]:
        response = await client.get("/v1/tenant", headers={TENANT_HEADER: tenant})
        assert (
            response.status_code == 404 and response.json()["error"]["code"] == "tenant_not_found"
        )
