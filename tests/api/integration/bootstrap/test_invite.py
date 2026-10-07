"""``make invite``: the operator creates a team and invites its first admin (AD-22)."""

from types import SimpleNamespace

import pytest
from sqlalchemy import text

from agilina_api.bootstrap.invite import invite
from agilina_api.shared_kernel import DomainError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import next_id
from tests.api.integration.world import TOKENS, World

pytestmark = pytest.mark.integration


@pytest.fixture
def container(session_factory):
    world = World(session_factory)
    return world, SimpleNamespace(
        issue_invitation=world.issue, create_team=world.create_team, team_queries=world.team_queries
    )


async def test_the_operator_creates_a_team_without_an_author_and_its_first_admin_gets_the_link(
    container, engine
):
    world, services = container

    await invite(
        services,
        email="julian@example.test",
        full_name="Julián Torres",
        role=TeamRole.ADMIN,
        language=Language.ES,
        team_name="Atlas",
        team_id=None,
    )

    async with engine.connect() as connection:
        team = (
            await connection.execute(text("SELECT name, language::text, created_by FROM team"))
        ).one()
        invitation = (
            await connection.execute(text("SELECT role::text, created_by FROM invitation"))
        ).one()
    assert tuple(team) == ("Atlas", "es", None)  # AD-22: created_by is NULL for the operator
    assert tuple(invitation) == ("admin", None)
    [message] = world.mailer.sent
    assert message.to == "julian@example.test" and f"#t={TOKENS[0]}" in message.text_body
    assert message.subject == "invitation:es"


async def test_one_more_person_can_be_invited_to_an_existing_team_in_its_language(container):
    world, services = container
    team_id = await world.a_team("Atlas", Language.EN)

    await invite(
        services,
        email="laura@example.test",
        full_name="Laura Méndez",
        role=TeamRole.MEMBER,
        language=Language.ES,  # ignored: the team's language wins
        team_name=None,
        team_id=team_id,
    )

    assert world.mailer.sent[0].subject == "invitation:en"
    assert "team_name=Atlas" in world.mailer.sent[0].text_body


async def test_an_unknown_team_id_is_refused(container):
    _, services = container

    with pytest.raises(DomainError, match="no team"):
        await invite(
            services,
            email="a@example.test",
            full_name="Ana",
            role=TeamRole.MEMBER,
            language=Language.EN,
            team_name=None,
            team_id=next_id(),
        )


async def test_inviting_the_same_person_twice_revokes_the_first_link_and_says_so(
    container, engine, capsys
):
    world, services = container
    team_id = await world.a_team()
    options = {
        "email": "julian@example.test",
        "full_name": "Julián",
        "role": TeamRole.ADMIN,
        "language": Language.ES,
        "team_name": None,
        "team_id": team_id,
    }
    await invite(services, **options)
    assert "revoked" not in capsys.readouterr().out

    await invite(services, **options)

    assert "previous invitation to that email was revoked" in capsys.readouterr().out
    async with engine.connect() as connection:
        statuses = (
            await connection.execute(
                text("SELECT status::text FROM invitation ORDER BY created_at")
            )
        ).scalars()
        assert sorted(statuses) == ["pending", "revoked"]
