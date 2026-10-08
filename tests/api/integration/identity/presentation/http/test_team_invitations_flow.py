"""HU-06 end to end over HTTP: an admin invites people to their team (criterion 2), with a
real PostgreSQL, the real email templates and the mailer doubled.

Someone without an account receives the activation link of HU-02 and, activating it, joins
with the chosen role; an existing account joins at once and receives a notice without a
link; a current member is refused; inviting again invalidates the previous link; and if the
email cannot be sent nothing is stored. The Keycloak token check (HU-03) is doubled by
``FakeAuthenticatedUsers``.
"""

import re
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.presentation.http import dependencies as deps
from agilina_api.shared.infrastructure.mail.renderer import JinjaEmailRenderer
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.presentation.http import dependencies as teams_deps
from agilina_shared.enums import Language
from tests.api.builders import AppUserBuilder, TeamBuilder
from tests.api.doubles import FakeAuthenticatedUsers
from tests.api.integration.support import stored_team, stored_user
from tests.api.integration.world import PASSWORD, TOKENS, World

pytestmark = pytest.mark.integration

TOKEN_DIEGO = "token-of-diego"
ACTIVATION_LINK = re.compile(r"https://app\.test/activate#t=([A-Za-z0-9_-]{43})")


def _returning(value):
    return lambda: value


class Invitations:
    """Atlas (in Spanish) is administered by Diego, who invites people over HTTP."""

    def __init__(self, world: World, team, diego) -> None:
        self.world, self.team, self.diego = world, team, diego
        app = create_app()
        overrides = {
            deps.get_invite_to_team_handler: world.invite_to_team,
            deps.get_invitation_status_handler: world.status,
            deps.get_activate_account_handler: world.activate,
            teams_deps.get_list_team_members_handler: world.list_members,
            get_authenticated_users: FakeAuthenticatedUsers({TOKEN_DIEGO: diego.id}),
            get_team_access: world.team_queries,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://tests")

    async def invite(self, email: str = "julian@example.test", **body):
        return await self.client.post(
            "/v1/users/invitations",
            params={"team_id": str(self.team.id)},
            json={"full_name": "Julián Torres", "email": email, **body},
            headers={"Authorization": f"Bearer {TOKEN_DIEGO}"},
        )

    async def members(self) -> list[tuple[str, str]]:
        response = await self.client.get(
            "/v1/users",
            params={"team_id": str(self.team.id)},
            headers={"Authorization": f"Bearer {TOKEN_DIEGO}"},
        )
        return [(m["email"], m["role"]) for m in response.json()["users"]]


@pytest.fixture
async def invitations(session_factory) -> AsyncIterator[Invitations]:
    diego = await stored_user(
        session_factory, AppUserBuilder().with_email("diego@example.test").named("Diego Rojas")
    )
    team = await stored_team(
        session_factory, TeamBuilder().named("Atlas").in_language(Language.ES).with_admin(diego.id)
    )
    invitations = Invitations(World(session_factory, JinjaEmailRenderer()), team, diego)
    yield invitations
    await invitations.client.aclose()


async def _scalar(engine, sql: str):
    async with engine.connect() as connection:
        return (await connection.execute(text(sql))).scalar_one()


async def test_a_person_without_account_gets_the_link_and_joins_with_the_chosen_role(
    invitations, engine
):
    response = await invitations.invite(role="admin")

    assert response.status_code == 201 and response.json() == {"outcome": "invitation_sent"}
    [message] = invitations.world.mailer.sent
    assert message.to == "julian@example.test"
    assert message.subject == "Te invitaron a Atlas en Agilina"
    assert "Diego Rojas" in message.text_body
    match = ACTIVATION_LINK.search(message.text_body)
    assert match is not None and match.group(0) in (message.html_body or "")
    token = match.group(1)
    assert token == TOKENS[0]
    assert token not in await _scalar(engine, "SELECT token_hash FROM invitation")

    activated = await invitations.client.post(
        "/v1/invitations/activate",
        json={"token": token, "password": PASSWORD, "confirmation": PASSWORD},
    )

    assert activated.status_code == 201 and activated.json()["role"] == "admin"
    assert await invitations.members() == [
        ("diego@example.test", "admin"),
        ("julian@example.test", "admin"),
    ]


async def test_the_role_is_member_unless_the_admin_chooses_another(invitations):
    await invitations.invite()

    status = await invitations.client.post("/v1/invitations/status", json={"token": TOKENS[0]})

    assert status.status_code == 200 and status.json()["role"] == "member"


async def test_an_existing_account_joins_at_once_and_gets_a_notice_without_a_link(
    invitations, engine, session_factory
):
    await stored_user(
        session_factory, AppUserBuilder().with_email("julian@example.test").named("Julián")
    )

    response = await invitations.invite(email="JULIAN@example.test")

    assert response.status_code == 201 and response.json() == {"outcome": "member_added"}
    assert await _scalar(engine, "SELECT count(*) FROM invitation") == 0
    assert ("julian@example.test", "member") in await invitations.members()
    [message] = invitations.world.mailer.sent
    assert message.subject == "Ahora formas parte de Atlas en Agilina"
    assert f"https://app.test/teams/{invitations.team.id}" in message.text_body
    for version in (message.text_body, message.html_body or ""):
        assert "/activate" not in version and "#t=" not in version


async def test_a_current_member_is_refused_and_nothing_is_sent(invitations, engine):
    response = await invitations.invite(email="diego@example.test")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_a_team_member"
    assert invitations.world.mailer.sent == []
    assert await _scalar(engine, "SELECT count(*) FROM team_member") == 1
    assert await _scalar(engine, "SELECT count(*) FROM invitation") == 0


async def test_inviting_again_invalidates_the_previous_link(invitations, engine):
    await invitations.invite()
    await invitations.invite()

    old = await invitations.client.post("/v1/invitations/status", json={"token": TOKENS[0]})
    used = await invitations.client.post(
        "/v1/invitations/activate",
        json={"token": TOKENS[0], "password": PASSWORD, "confirmation": PASSWORD},
    )
    new = await invitations.client.post("/v1/invitations/status", json={"token": TOKENS[1]})

    assert old.status_code == 410 and old.json()["error"]["code"] == "invitation_revoked"
    assert used.status_code == 410 and used.json()["error"]["code"] == "invitation_revoked"
    assert new.status_code == 200 and new.json()["status"] == "pending"
    assert len(invitations.world.mailer.sent) == 2
    assert await _scalar(engine, "SELECT count(*) FROM invitation WHERE status = 'revoked'") == 1


async def test_a_disabled_account_is_refused(invitations, session_factory):
    await stored_user(
        session_factory, AppUserBuilder().with_email("julian@example.test").disabled()
    )

    response = await invitations.invite()

    assert response.status_code == 409 and response.json()["error"]["code"] == "account_disabled"
    assert invitations.world.mailer.sent == []


async def test_if_the_email_cannot_be_sent_the_answer_is_502_and_nothing_is_stored(
    invitations, engine
):
    invitations.world.mailer.fail = True

    response = await invitations.invite()

    assert response.status_code == 502 and response.json()["error"]["code"] == "mail_unavailable"
    assert await _scalar(engine, "SELECT count(*) FROM invitation") == 0


@pytest.mark.parametrize(
    ("email", "full_name", "code"),
    [
        ("not-an-email", "Julián", "invalid_email"),
        ("julian@example.test", "  ", "invalid_full_name"),
    ],
)
async def test_invalid_data_answers_422_and_stores_nothing(
    invitations, engine, email, full_name, code
):
    response = await invitations.invite(email=email, full_name=full_name)

    assert response.status_code == 422 and response.json()["error"]["code"] == code
    assert await _scalar(engine, "SELECT count(*) FROM invitation") == 0
