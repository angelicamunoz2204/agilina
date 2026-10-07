"""Which tenant a request is about, as a FastAPI dependency (AD-29).

Every request that touches a tenant's data names it in the ``X-Agilina-Tenant`` header. A
request without it is a ``400``; a tenant that does not exist, is suspended or is not even a
valid name is a ``404``, the same for all three so that nobody can tell which tenants exist.

The catalog is declared here and provided by the composition root, so this layer never
imports the infrastructure one.
"""

from fastapi import Depends, Header

from agilina_api.shared.application.tenancy import (
    Tenant,
    TenantDirectory,
    TenantNotFoundError,
    TenantRequiredError,
)

TENANT_HEADER = "X-Agilina-Tenant"


def get_tenant_directory() -> TenantDirectory:
    raise NotImplementedError("Wired by the composition root")


async def current_tenant(
    name: str | None = Header(default=None, alias=TENANT_HEADER),
    directory: TenantDirectory = Depends(get_tenant_directory),
) -> Tenant:
    """The active tenant the request names."""
    if name is None or not name:
        raise TenantRequiredError(f"The request carries no {TENANT_HEADER} header")
    tenant = await directory.find_active(name)
    if tenant is None:
        raise TenantNotFoundError("The tenant does not exist or is not active")
    return tenant
