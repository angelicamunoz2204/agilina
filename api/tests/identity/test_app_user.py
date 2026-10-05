"""The AppUser aggregate anchors the domain's references to a Keycloak identity."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from agilina_api.identity.domain.errors import InvalidFullNameError
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


def _register(**overrides) -> AppUser:
    fields = {
        "user_id": uuid4(),
        "keycloak_subject": "3f2b-subject",
        "email": Email("julian@example.test"),
        "full_name": "Julián Torres",
        "now": NOW,
    }
    fields.update(overrides)
    return AppUser.register(**fields)


def test_a_registered_user_is_active_and_keeps_its_keycloak_subject():
    user = _register(keycloak_subject="  3f2b-subject  ")

    assert user.is_active is True
    assert user.keycloak_subject == "3f2b-subject"
    assert user.created_at == NOW
    assert user.email == Email("julian@example.test")


def test_a_user_needs_a_name_and_a_keycloak_subject():
    with pytest.raises(InvalidFullNameError):
        _register(full_name="  ")
    with pytest.raises(ValueError, match="Keycloak subject"):
        _register(keycloak_subject="  ")
