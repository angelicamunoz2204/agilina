"""One object graph per tenant, built the first time the tenant is used (AD-29).

Each tenant has its own database (and so its own connection pool), its own realm and its own
secret, so each gets its own ``Container``. They are kept for the life of the process and
closed when the API stops.
"""

import asyncio
from collections.abc import Callable

from fastapi import Depends, Request

from agilina_api.bootstrap.container import Container, build_container
from agilina_api.shared.application.tenancy import Tenant
from agilina_api.shared.infrastructure.settings import Settings
from agilina_api.shared.presentation.http.tenancy import current_tenant


class TenantContainers:
    def __init__(
        self,
        settings: Settings,
        build: Callable[[Settings, Tenant], Container] = build_container,
    ) -> None:
        self._settings = settings
        self._build = build
        self._containers: dict[str, Container] = {}
        self._lock = asyncio.Lock()

    async def for_tenant(self, tenant: Tenant) -> Container:
        """The graph of ``tenant``: always the same one for the same tenant."""
        async with self._lock:
            container = self._containers.get(tenant.slug)
            if container is None:
                container = self._build(self._settings, tenant)
                self._containers[tenant.slug] = container
            return container

    async def aclose(self) -> None:
        containers, self._containers = list(self._containers.values()), {}
        for container in containers:
            await container.aclose()


async def current_container(
    request: Request, tenant: Tenant = Depends(current_tenant)
) -> Container:
    """The graph of the tenant the request names. Everything that touches a tenant's data
    reaches it through here, which is why every such route needs the tenant header."""
    containers: TenantContainers = request.app.state.tenant_containers
    return await containers.for_tenant(tenant)


def from_container[T](select: Callable[[Container], T]) -> Callable[[Container], T]:
    """A FastAPI provider of one piece of the request's tenant container."""

    def provide(container: Container = Depends(current_container)) -> T:
        return select(container)

    return provide
