"""The composition root builds the whole object graph without connecting to anything."""

from agilina_api.bootstrap.container import build_container
from agilina_api.shared.infrastructure.settings import get_settings


def test_the_graph_is_built_without_postgres_keycloak_or_a_mail_server():
    container = build_container(get_settings())

    assert container.activate_account is not None
    assert container.issue_invitation is not None
    assert container.request_new_invitation is not None
    assert container.invitation_status is not None
    assert container.create_team is not None


async def test_closing_the_container_closes_the_keycloak_client():
    container = build_container(get_settings())

    await container.aclose()

    assert container.identity_provider._client.is_closed is True  # noqa: SLF001
