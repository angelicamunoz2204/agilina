"""The catalog of tenants: what it reads, what it hides and how long it remembers."""

from datetime import timedelta
from types import SimpleNamespace

from agilina_api.shared.infrastructure.tenancy.sql_tenant_directory import (
    CACHE_LIFETIME,
    SqlTenantDirectory,
)
from agilina_shared.enums import Language
from tests.api.doubles import FakeClock


class _Catalog:
    """A session factory over the rows of the ``tenant`` table that are active."""

    def __init__(self, *rows: tuple[str, str, str]) -> None:
        self.rows = list(rows)
        self.reads = 0

    def __call__(self) -> "_Catalog":
        return self

    async def __aenter__(self) -> "_Catalog":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def execute(self, statement: object) -> "_Result":
        self.reads += 1
        return _Result(
            [
                SimpleNamespace(slug=slug, display_name=name, language=language, status="active")
                for slug, name, language in self.rows
            ]
        )


class _Result:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self._rows


def _directory(catalog: _Catalog, clock: FakeClock | None = None) -> SqlTenantDirectory:
    return SqlTenantDirectory(catalog, clock or FakeClock())  # type: ignore[arg-type]


async def test_an_active_tenant_is_found_with_its_name_and_language():
    directory = _directory(
        _Catalog(("ecomoda", "Ecomoda", "es"), ("acme", "ACME Corporation", "en"))
    )

    tenant = await directory.find_active("ecomoda")

    assert tenant is not None
    assert (tenant.slug, tenant.display_name, tenant.language) == (
        "ecomoda",
        "Ecomoda",
        Language.ES,
    )
    assert tenant.is_active


async def test_a_tenant_that_is_not_in_the_catalog_is_not_found():
    assert (
        await _directory(_Catalog(("acme", "ACME Corporation", "en"))).find_active("globex") is None
    )


async def test_a_name_that_is_not_a_slug_is_not_found_without_asking_the_database():
    catalog = _Catalog(("acme", "ACME Corporation", "en"))

    for name in ["", "Acme", "ac me", "acme'; DROP TABLE tenant; --", "platform"]:
        assert await _directory(catalog).find_active(name) is None

    assert catalog.reads == 0


async def test_every_active_tenant_is_listed_by_slug():
    directory = _directory(
        _Catalog(("ecomoda", "Ecomoda", "es"), ("acme", "ACME Corporation", "en"))
    )

    assert [tenant.slug for tenant in await directory.list_active()] == ["ecomoda", "acme"]


async def test_the_catalog_is_read_once_and_remembered_for_a_while():
    catalog = _Catalog(("acme", "ACME Corporation", "en"))
    clock = FakeClock()
    directory = _directory(catalog, clock)

    await directory.find_active("acme")
    clock.advance(seconds=CACHE_LIFETIME.total_seconds() - 1)
    await directory.find_active("acme")

    assert catalog.reads == 1


async def test_a_tenant_that_was_suspended_stops_answering_after_the_cache_expires():
    catalog = _Catalog(("acme", "ACME Corporation", "en"))
    clock = FakeClock()
    directory = _directory(catalog, clock)
    assert await directory.find_active("acme") is not None

    catalog.rows.clear()  # suspended in the catalog
    assert await directory.find_active("acme") is not None  # still remembered
    clock.advance(seconds=CACHE_LIFETIME.total_seconds())

    assert await directory.find_active("acme") is None
    assert catalog.reads == 2


def test_the_cache_lasts_half_a_minute():
    assert CACHE_LIFETIME == timedelta(seconds=30)
