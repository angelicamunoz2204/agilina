"""Builder of ``Tenant``."""

from dataclasses import dataclass, replace
from typing import Self

from agilina_api.shared.application.tenancy import Tenant, TenantStatus
from agilina_shared.enums import Language


@dataclass(frozen=True)
class TenantBuilder:
    """ACME Corporation, active, in English (one of the two development tenants)."""

    slug: str = "acme"
    display_name: str = "ACME Corporation"
    language: Language = Language.EN
    status: TenantStatus = TenantStatus.ACTIVE

    def with_slug(self, slug: str) -> Self:
        return replace(self, slug=slug)

    def named(self, display_name: str) -> Self:
        return replace(self, display_name=display_name)

    def in_language(self, language: Language) -> Self:
        return replace(self, language=language)

    def suspended(self) -> Self:
        return replace(self, status=TenantStatus.SUSPENDED)

    def ecomoda(self) -> Self:
        """The second development tenant: Ecomoda, in Spanish."""
        return replace(self, slug="ecomoda", display_name="Ecomoda", language=Language.ES)

    def build(self) -> Tenant:
        return Tenant(
            slug=self.slug,
            display_name=self.display_name,
            language=self.language,
            status=self.status,
        )
