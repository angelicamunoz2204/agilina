"""The composition root builds the whole object graph without connecting to anything."""

from agilina_api.bootstrap.authentication import ClosedAuthenticatedUsers
from agilina_api.bootstrap.container import build_container
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


def test_until_login_exists_no_token_is_trusted():
    container = build_container(get_settings())

    assert isinstance(container.authenticated_users, ClosedAuthenticatedUsers)


def test_the_membership_is_checked_against_the_stored_teams():
    container = build_container(get_settings())

    assert container.team_access is container.team_queries


async def test_closing_the_container_closes_the_keycloak_client():
    container = build_container(get_settings())

    await container.aclose()

    assert container.identity_provider._client.is_closed is True  # noqa: SLF001
