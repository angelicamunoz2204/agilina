"""The composition root builds the whole object graph without connecting to anything."""

from agilina_api.bootstrap.container import build_container
from agilina_api.identity.infrastructure.keycloak.authenticated_users import (
    KeycloakAuthenticatedUsers,
)
from agilina_api.shared.infrastructure.settings import get_settings


def test_the_graph_is_built_without_postgres_keycloak_or_a_mail_server():
    container = build_container(get_settings())

    assert container.activate_account is not None
    assert container.issue_invitation is not None
    assert container.request_new_invitation is not None
    assert container.invitation_status is not None
    assert container.create_team is not None
    assert container.create_team_as_admin is not None
    assert container.list_my_teams is not None
    assert container.get_team is not None
    assert container.invite_to_team is not None
    assert container.list_team_members is not None
    assert container.change_member_role is not None
    assert container.remove_member is not None


def test_the_invitation_links_open_the_web_from_its_public_url():
    """The activation link goes to ``/activate`` and the notice to an existing account to
    the team, both under ``AGILINA_WEB_PUBLIC_URL`` (HU-02 and HU-06)."""
    settings = get_settings().model_copy(update={"web_public_url": "https://agilina.example/"})

    container = build_container(settings)

    assert container.issue_invitation._activation_url == "https://agilina.example/activate"  # noqa: SLF001
    assert container.invite_to_team._teams_url == "https://agilina.example/teams"  # noqa: SLF001


def test_the_tokens_are_validated_against_the_realm_by_its_public_url(monkeypatch):
    monkeypatch.setenv("AGILINA_KEYCLOAK_URL", "http://keycloak:8080")
    monkeypatch.setenv("AGILINA_KEYCLOAK_PUBLIC_URL", "http://localhost:8080/")
    get_settings.cache_clear()

    container = build_container(get_settings())

    assert isinstance(container.authenticated_users, KeycloakAuthenticatedUsers)
    verifier = container.access_token_verifier
    # The issuer a token carries is the public one; the keys are read through the internal one.
    assert verifier._issuer == "http://localhost:8080/realms/agilina"  # noqa: SLF001
    assert verifier._audience == "agilina-api"  # noqa: SLF001
    assert verifier._jwks_url == (  # noqa: SLF001
        "http://keycloak:8080/realms/agilina/protocol/openid-connect/certs"
    )


def test_the_membership_is_checked_against_the_stored_teams():
    container = build_container(get_settings())

    assert container.team_access is container.team_queries


async def test_closing_the_container_closes_the_keycloak_client():
    container = build_container(get_settings())

    await container.aclose()

    assert container.identity_provider._client.is_closed is True  # noqa: SLF001
    assert container.access_token_verifier._client.is_closed is True  # noqa: SLF001
