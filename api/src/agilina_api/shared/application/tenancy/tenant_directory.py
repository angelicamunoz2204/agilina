from typing import Protocol

from agilina_api.shared.application.tenancy.tenant import Tenant


class TenantDirectory(Protocol):
    """The catalog of tenants."""

    async def find_active(self, slug: str) -> Tenant | None:
        """The tenant, only while it is active: ``None`` for one that does not exist, one
        that is suspended and a slug that is not valid."""
        ...

    async def list_active(self) -> list[Tenant]:
        """Every active tenant, by slug."""
        ...
