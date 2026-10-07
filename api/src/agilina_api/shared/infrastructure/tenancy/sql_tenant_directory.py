"""The catalog of tenants in the platform's database."""

from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.shared.application.ports import Clock
from agilina_api.shared.application.tenancy import (
    Tenant,
    TenantDirectory,
    TenantStatus,
    is_valid_slug,
)
from agilina_shared.enums import Language

CACHE_LIFETIME = timedelta(seconds=30)

_ACTIVE_TENANTS = text(
    "SELECT slug, display_name, language, status FROM tenant WHERE status = 'active' ORDER BY slug"
)


class SqlTenantDirectory(TenantDirectory):
    """Reads the ``tenant`` table. The answer is kept for 30 seconds, because every request
    asks for its tenant; so a tenant that was suspended in the catalog keeps answering for at
    most that long."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        clock: Clock,
        cache_lifetime: timedelta = CACHE_LIFETIME,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock
        self._cache_lifetime = cache_lifetime
        self._active: dict[str, Tenant] = {}
        self._read_at: datetime | None = None

    async def find_active(self, slug: str) -> Tenant | None:
        if not is_valid_slug(slug):
            return None
        return (await self._tenants()).get(slug)

    async def list_active(self) -> list[Tenant]:
        return list((await self._tenants()).values())

    async def _tenants(self) -> dict[str, Tenant]:
        now = self._clock.now()
        if self._read_at is None or now - self._read_at >= self._cache_lifetime:
            async with self._session_factory() as session:
                rows = (await session.execute(_ACTIVE_TENANTS)).all()
            self._active = {
                row.slug: Tenant(
                    slug=row.slug,
                    display_name=row.display_name,
                    language=Language(row.language),
                    status=TenantStatus(row.status),
                )
                for row in rows
            }
            self._read_at = now
        return self._active
