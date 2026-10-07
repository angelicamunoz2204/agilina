"""HU-02 end to end over HTTP: real PostgreSQL behind the API, Keycloak and the mailer doubled.

The story as the criteria tell it: an operator creates a team and invites its first admin,
the person opens the link, chooses a password and the account is created in its team; the
link works once; a link that no longer works can be reported to the admins.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.presentation.http import dependencies as deps
from agilina_shared.enums import Language, TeamRole
from tests.api.integration.world import PASSWORD, TOKENS, World

pytestmark = pytest.mark.integration


def _returning(handler):
    return lambda: handler


@pytest.fixture
def world(session_factory) -> World:
    return World(session_factory)


@pytest.fixture
def client(world: World) -> AsyncClient:
    app = create_app()
    app.dependency_overrides[deps.get_invitation_status_handler] = _returning(world.status)
    app.dependency_overrides[deps.get_activate_account_handler] = _returning(world.activate)
    app.dependency_overrides[deps.get_request_new_invitation_handler] = _returning(
        world.request_new
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://tests")


async def _post(client: AsyncClient, path: str, **body):
    return await client.post(f"/v1/invitations/{path}", json=body)


async def _scalar(engine, sql: str):
    async with engine.connect() as connection:
        return (await connection.execute(text(sql))).scalar_one()


async def test_the_whole_story_of_the_first_admin(world, client, engine):
    team_id = await world.a_team("Atlas", Language.ES)
    await world.invite(team_id, email="julian@example.test", role=TeamRole.ADMIN)
    link_token = TOKENS[0]
    assert f"#t={link_token}" in world.mailer.sent[0].text_body  # what the person receives

    # 1. the activation page asks about the link
    status = await _post(client, "status", token=link_token)
    assert status.status_code == 200 and status.json()["status"] == "pending"
    assert status.json()["email"] == "julian@example.test"

    # 2. the person chooses a password
    activated = await _post(
        client, "activate", token=link_token, password=PASSWORD, confirmation=PASSWORD
    )
    assert activated.status_code == 201
    assert activated.json() == {
        "email": "julian@example.test",
        "team_id": str(team_id),
        "role": "admin",
    }

    # 3. the account exists, in its team, with the role the operator chose
    assert await _scalar(engine, "SELECT count(*) FROM app_user") == 1
    assert (
        await _scalar(
            engine,
            f"SELECT role::text FROM team_member WHERE team_id = '{team_id}'",  # noqa: S608 - test constant
        )
        == "admin"
    )
    assert world.provider.created == [("julian@example.test", "Julián Torres", PASSWORD)]

    # 4. the link works once
    again = await _post(client, "status", token=link_token)
    assert again.status_code == 410 and again.json()["error"]["code"] == "invitation_used"
    second = await _post(
        client, "activate", token=link_token, password=PASSWORD, confirmation=PASSWORD
    )
    assert second.status_code == 410
    assert await _scalar(engine, "SELECT count(*) FROM app_user") == 1


async def test_a_link_that_expired_can_be_reported_and_the_admin_hears_about_it(world, client):
    team_id = await world.a_team("Atlas", Language.EN)
    await world.invite(team_id, email="diego@example.test", role=TeamRole.ADMIN)  # token A
    await _post(client, "activate", token=TOKENS[0], password=PASSWORD, confirmation=PASSWORD)
    await world.invite(team_id, email="laura@example.test", role=TeamRole.MEMBER)  # token B
    world.mailer.sent.clear()
    world.clock.advance(days=8)

    expired = await _post(client, "status", token=TOKENS[1])
    assert expired.status_code == 410 and expired.json()["error"]["code"] == "invitation_expired"

    asked = await _post(client, "request-new", token=TOKENS[1])

    assert asked.status_code == 202
    [message] = world.mailer.sent
    assert message.to == "diego@example.test" and "laura@example.test" in message.text_body


async def test_a_refused_password_leaves_the_database_untouched_and_the_link_usable(
    world, client, engine
):
    team_id = await world.a_team()
    await world.invite(team_id)
    world.provider.refuse_password("min_length")

    refused = await _post(
        client, "activate", token=TOKENS[0], password="short", confirmation="short"
    )

    assert refused.status_code == 422 and refused.json()["error"]["details"]["reasons"] == [
        "min_length"
    ]
    assert await _scalar(engine, "SELECT count(*) FROM app_user") == 0
    assert (await _post(client, "status", token=TOKENS[0])).status_code == 200


async def test_an_altered_link_is_not_found_over_http(world, client):
    await world.invite(await world.a_team())

    response = await _post(client, "status", token=TOKENS[0][:-1] + "Z")

    assert (
        response.status_code == 404 and response.json()["error"]["code"] == "invitation_not_found"
    )
