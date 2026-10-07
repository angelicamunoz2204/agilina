"""Tenants: the organizations the platform serves (AD-29).

A tenant has its own database, its own realm in Keycloak and its own login. Teams live inside
a tenant, in its database, and keep being isolated from each other by ``team_id``. The
platform keeps a catalog of the tenants that exist: the administrator adds one with
``make tenant-add`` and suspends or reactivates it in the catalog.

The tenant is chosen at the edge, once per request, and what lies behind (use cases,
repositories, queries) neither knows nor repeats it.
"""

from agilina_api.shared.application.tenancy.tenant import Tenant
from agilina_api.shared.application.tenancy.tenant_directory import TenantDirectory
from agilina_api.shared.application.tenancy.tenant_not_found_error import TenantNotFoundError
from agilina_api.shared.application.tenancy.tenant_required_error import TenantRequiredError
from agilina_api.shared.application.tenancy.tenant_slug import (
    RESERVED_SLUGS,
    SLUG_PATTERN,
    is_valid_slug,
)
from agilina_api.shared.application.tenancy.tenant_status import TenantStatus

__all__ = [
    "RESERVED_SLUGS",
    "SLUG_PATTERN",
    "Tenant",
    "TenantDirectory",
    "TenantNotFoundError",
    "TenantRequiredError",
    "TenantStatus",
    "is_valid_slug",
]
