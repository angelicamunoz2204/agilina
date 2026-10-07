"""The helpers that create and migrate the databases of the platform (no database needed)."""

import pytest

from agilina_api.shared.infrastructure.migrations import (
    alembic_config,
    database_name,
)


def test_the_name_of_a_database_comes_from_its_url():
    assert database_name("postgresql+psycopg://u:p@h:5432/agilina_acme") == "agilina_acme"


def test_a_url_without_a_database_is_an_error():
    with pytest.raises(ValueError, match="no database"):
        database_name("postgresql+psycopg://u:p@h:5432")


@pytest.mark.parametrize("environment", ["platform", "tenant"])
def test_each_kind_of_database_has_its_own_migrations_and_receives_its_url(environment):
    config = alembic_config(environment, "postgresql+psycopg://u:p@h/db")

    assert config.get_main_option("script_location").endswith(f"migrations/{environment}")
    assert config.attributes["url"] == "postgresql+psycopg://u:p@h/db"
