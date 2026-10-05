"""The identity use cases against a real PostgreSQL, with Keycloak and the mailer doubled.

What the in-memory tests cannot show: that the transaction really spans the invitation,
the user and the membership, that a refused activation really leaves nothing behind, and
that two simultaneous activations of one link let only one through.
"""

import asyncio

import pytest
from sqlalchemy import text

from agilina_api.identity.application.commands.activate_account import (
    ActivateAccount,
)
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitation,
)
from agilina_api.identity.application.errors import PasswordPolicyError
from agilina_api.identity.domain.errors import (
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    PendingInvitationAlreadyExistsError,
    UnknownTeamError,
    UserAlreadyExistsError,
)
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import AppUserBuilder, next_id
from tests.api.integration.support import stored_user
from tests.api.integration.world import PASSWORD, TOKEN, TOKENS, World

pytestmark = pytest.mark.integration


@pytest.fixture
def world(session_factory) -> World:
    return World(session_factory)


async def _count(engine, table, where="true"):
    statement = text(f"SELECT count(*) FROM {table} WHERE {where}")  # noqa: S608 - constants of the tests
    async with engine.connect() as connection:
        return (await connection.execute(statement)).scalar_one()


async def test_an_operator_creates_a_team_and_invites_its_first_admin_end_to_end(world, engine):
    team_id = await world.a_team()
    await world.invite(team_id)

    result = await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))

    assert (result.team_id, result.role) == (team_id, TeamRole.ADMIN)
    assert await _count(engine, "app_user") == 1
    assert (
        await _count(
            engine, "team_member", f"team_id = '{team_id}' AND role = 'admin' AND status = 'active'"
        )
        == 1
    )
    assert (
        await _count(engine, "invitation", "status = 'accepted' AND accepted_user_id IS NOT NULL")
        == 1
    )
    assert world.provider.created == [("julian@example.test", "Julián Torres", PASSWORD)]


async def test_the_invitation_email_carries_the_link_and_only_the_hash_is_in_the_database(
    world, engine
):
    team_id = await world.a_team()
    await world.invite(team_id)

    assert f"#t={TOKEN}" in world.mailer.sent[0].text_body
    async with engine.connect() as connection:
        stored = (await connection.execute(text("SELECT token_hash FROM invitation"))).scalar_one()
    assert TOKEN not in stored


async def test_inviting_to_a_team_that_does_not_exist_is_refused_and_sends_nothing(world):
    with pytest.raises(UnknownTeamError):
        await world.invite(next_id())

    assert world.mailer.sent == []


async def test_a_second_valid_invitation_for_the_same_person_is_refused(world):
    team_id = await world.a_team()
    await world.invite(team_id)

    with pytest.raises(PendingInvitationAlreadyExistsError):
        await world.invite(team_id)


async def test_an_expired_invitation_is_closed_and_a_new_one_can_be_issued(world, engine):
    team_id = await world.a_team()
    await world.invite(team_id)
    world.clock.advance(days=8)

    await world.invite(team_id)

    assert await _count(engine, "invitation", "status = 'expired'") == 1
    assert await _count(engine, "invitation", "status = 'pending'") == 1


async def test_a_refused_password_leaves_nothing_behind_and_the_link_still_works(world, engine):
    team_id = await world.a_team()
    await world.invite(team_id)
    world.provider.refuse_password("min_length")

    with pytest.raises(PasswordPolicyError):
        await world.activate.handle(ActivateAccount(token=TOKEN, password="short"))

    assert await _count(engine, "app_user") == 0 and await _count(engine, "team_member") == 0
    assert await _count(engine, "invitation", "status = 'pending'") == 1
    world.provider.error = None
    await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))
    assert await _count(engine, "app_user") == 1


async def test_a_used_link_and_an_expired_one_cannot_be_used(world):
    team_id = await world.a_team()
    await world.invite(team_id)
    await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))
    with pytest.raises(InvitationAlreadyUsedError):
        await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))

    team_two = await world.a_team("Borealis")
    await world.invite(team_two, email="laura@example.test")
    world.clock.advance(days=8)
    with pytest.raises(InvitationExpiredError):
        await world.activate.handle(ActivateAccount(token=TOKENS[1], password=PASSWORD))


async def test_when_the_database_part_fails_the_keycloak_account_is_removed(
    world, engine, session_factory
):
    """Fail *after* Keycloak created the account: the subject it will return is already taken."""
    team_id = await world.a_team()
    await world.invite(team_id)
    # FakeIdentityProvider's first subject
    await stored_user(session_factory, AppUserBuilder().with_unique_email().with_subject("kc-1"))

    with pytest.raises(UserAlreadyExistsError):
        await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))

    assert world.provider.deleted == ["kc-1"]  # the account Keycloak created was undone
    assert await _count(engine, "app_user") == 1  # only the one that was already there
    assert await _count(engine, "team_member") == 0
    assert await _count(engine, "invitation", "status = 'pending'") == 1


async def test_two_simultaneous_activations_of_the_same_link_call_keycloak_only_once(world, engine):
    team_id = await world.a_team()
    await world.invite(team_id)

    results = await asyncio.gather(
        world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD)),
        world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD)),
        return_exceptions=True,
    )

    assert sum(1 for r in results if not isinstance(r, Exception)) == 1
    assert sum(1 for r in results if isinstance(r, InvitationAlreadyUsedError)) == 1
    assert len(world.provider.created) == 1 and await _count(engine, "app_user") == 1


async def test_the_admins_of_the_team_are_told_when_a_link_expired(world):
    team_id = await world.a_team(language=Language.EN)
    await world.invite(team_id, email="diego@example.test")  # token A: Diego, the first admin
    await world.activate.handle(ActivateAccount(token=TOKENS[0], password=PASSWORD))
    await world.invite(team_id, email="laura@example.test", role=TeamRole.MEMBER)  # token B
    world.mailer.sent.clear()
    world.clock.advance(days=8)

    await world.request_new.handle(RequestNewInvitation(token=TOKENS[1]))

    [message] = world.mailer.sent
    assert message.to == "diego@example.test" and message.subject == "new_invitation_request:en"
    assert "requester_email=laura@example.test" in message.text_body
    assert "reason=expired" in message.text_body
