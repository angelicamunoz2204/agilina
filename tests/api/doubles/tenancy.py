"""A double of the catalog of tenants."""

from agilina_api.shared.application.tenancy import Tenant


class FakeTenantDirectory:
    """Knows the tenants the test gives it. Like the real catalog it only answers for the
    active ones: a suspended tenant, an unknown one and a slug that is not valid are all
    ``None``."""

    def __init__(self, *tenants: Tenant) -> None:
        self.tenants = list(tenants)
        self.asked: list[str] = []

    async def find_active(self, slug: str) -> Tenant | None:
        self.asked.append(slug)
        return next((t for t in self.tenants if t.slug == slug and t.is_active), None)

    async def list_active(self) -> list[Tenant]:
        return sorted((t for t in self.tenants if t.is_active), key=lambda t: t.slug)
