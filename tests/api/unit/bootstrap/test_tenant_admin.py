"""``make tenant-add``: what it refuses before touching anything."""

import sys

import pytest

from agilina_api.bootstrap import tenant_admin
from agilina_api.shared.infrastructure.settings import get_settings


@pytest.mark.parametrize(
    "slug", ["Acme", "a", "1acme", "ac-me", "platform", "admin", "api", "x" * 40]
)
def test_a_slug_that_cannot_be_a_database_or_a_realm_is_refused_with_the_reason(
    monkeypatch, capsys, slug
):
    monkeypatch.setattr(sys, "argv", ["tenant-add", "--slug", slug, "--name", "Whatever"])

    assert tenant_admin.main() == 1
    assert "is not a valid slug" in capsys.readouterr().err


def test_a_name_and_a_slug_are_both_needed(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tenant-add", "--slug", "acme"])

    with pytest.raises(SystemExit):
        tenant_admin.main()


def test_a_language_the_product_does_not_speak_is_refused(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["tenant-add", "--slug", "acme", "--name", "A", "--lang", "fr"]
    )

    with pytest.raises(SystemExit):
        tenant_admin.main()


def test_the_operator_signs_in_to_keycloak_as_its_administrator(monkeypatch):
    monkeypatch.setenv("KEYCLOAK_ADMIN", "root")
    monkeypatch.setenv("KEYCLOAK_ADMIN_PASSWORD", "the-password")
    monkeypatch.setenv("AGILINA_KEYCLOAK_URL", "http://keycloak:8080/")
    get_settings.cache_clear()

    provisioner = tenant_admin._provisioner(get_settings())  # noqa: SLF001

    assert provisioner._base_url == "http://keycloak:8080"  # noqa: SLF001
    assert provisioner._admin_user == "root"  # noqa: SLF001
    assert provisioner._admin_password == "the-password"  # noqa: SLF001
