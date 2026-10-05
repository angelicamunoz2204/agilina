"""The AppUser aggregate anchors the domain's references to a Keycloak identity."""

import pytest

from agilina_api.identity.domain.errors import InvalidFullNameError
from agilina_api.identity.domain.value_objects import Email
from tests.api.builders import NOW, AppUserBuilder


def test_a_registered_user_is_active_and_keeps_its_keycloak_subject():
    user = AppUserBuilder().with_subject("  3f2b-subject  ").build()

    assert user.is_active is True
    assert user.keycloak_subject == "3f2b-subject"
    assert user.created_at == NOW
    assert user.email == Email("julian@example.test")


def test_a_user_needs_a_name_and_a_keycloak_subject():
    with pytest.raises(InvalidFullNameError):
        AppUserBuilder().named("  ").build()
    with pytest.raises(ValueError, match="Keycloak subject"):
        AppUserBuilder().with_subject("  ").build()
