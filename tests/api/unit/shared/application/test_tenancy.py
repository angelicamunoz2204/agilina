"""What a tenant is called, and what the platform keeps for itself (AD-29)."""

import pytest

from agilina_api.shared.application.tenancy import TenantStatus, is_valid_slug
from tests.api.builders import TenantBuilder


@pytest.mark.parametrize("slug", ["acme", "ecomoda", "ab", "a1", "a" + "b" * 30, "acme2"])
def test_a_slug_is_lowercase_letters_and_digits_starting_with_a_letter(slug):
    assert is_valid_slug(slug)


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "a",  # too short
        "a" + "b" * 31,  # too long
        "1acme",  # starts with a digit
        "Acme",
        "ac me",
        "ac-me",  # a hyphen would not be a database name
        "ac_me",
        "acme;drop",
        "../acme",
        "ácme",
    ],
)
def test_anything_else_is_not_a_slug(slug):
    assert not is_valid_slug(slug)


@pytest.mark.parametrize("slug", ["platform", "admin", "api"])
def test_the_names_the_platform_keeps_for_itself_cannot_be_a_tenant(slug):
    assert not is_valid_slug(slug)


def test_a_tenant_is_active_unless_it_was_suspended():
    assert TenantBuilder().build().is_active
    assert TenantBuilder().build().status is TenantStatus.ACTIVE
    assert not TenantBuilder().suspended().build().is_active
