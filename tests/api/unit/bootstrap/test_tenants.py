"""One object graph per tenant, built the first time and kept (AD-29)."""

import asyncio

from agilina_api.bootstrap.tenants import TenantContainers
from agilina_api.shared.infrastructure.settings import get_settings
from tests.api.builders import TenantBuilder


class _Built:
    def __init__(self, tenant) -> None:
        self.tenant = tenant
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


def _containers() -> tuple[TenantContainers, list[str]]:
    built: list[str] = []

    def build(settings, tenant):
        built.append(tenant.slug)
        return _Built(tenant)

    return TenantContainers(get_settings(), build), built  # type: ignore[arg-type]


async def test_a_tenant_always_gets_the_same_graph():
    containers, built = _containers()
    acme = TenantBuilder().build()

    first = await containers.for_tenant(acme)
    second = await containers.for_tenant(acme)

    assert first is second
    assert built == ["acme"]


async def test_two_tenants_never_share_a_graph():
    containers, built = _containers()

    acme = await containers.for_tenant(TenantBuilder().build())
    ecomoda = await containers.for_tenant(TenantBuilder().ecomoda().build())

    assert acme is not ecomoda
    assert built == ["acme", "ecomoda"]


async def test_many_requests_at_once_for_a_new_tenant_build_its_graph_once():
    containers, built = _containers()
    acme = TenantBuilder().build()

    graphs = await asyncio.gather(*(containers.for_tenant(acme) for _ in range(20)))

    assert len({id(graph) for graph in graphs}) == 1
    assert built == ["acme"]


async def test_closing_closes_every_graph_and_forgets_them():
    containers, built = _containers()
    acme = await containers.for_tenant(TenantBuilder().build())
    ecomoda = await containers.for_tenant(TenantBuilder().ecomoda().build())

    await containers.aclose()
    await containers.for_tenant(TenantBuilder().build())

    assert acme.closed and ecomoda.closed  # type: ignore[attr-defined]
    assert built == ["acme", "ecomoda", "acme"]
