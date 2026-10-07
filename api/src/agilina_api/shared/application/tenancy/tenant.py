from dataclasses import dataclass

from agilina_api.shared.application.tenancy.tenant_status import TenantStatus
from agilina_shared.enums import Language


@dataclass(frozen=True)
class Tenant:
    slug: str
    display_name: str
    language: Language
    """The language by default of what the tenant shows before a team has chosen its own."""
    status: TenantStatus = TenantStatus.ACTIVE

    @property
    def is_active(self) -> bool:
        return self.status is TenantStatus.ACTIVE
