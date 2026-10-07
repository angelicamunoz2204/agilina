"""The identity use cases against a real PostgreSQL, with Keycloak and the mailer doubled.

What the in-memory tests cannot show: that the transaction really spans the invitation,
the user and the membership, that a refused activation really leaves nothing behind, and
that two simultaneous activations of one link let only one through. And, for HU-06, that an
admin's invitation points to their membership, and that a refused one rolls back the
pending invitation it had started to close.
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
from agilina_api.identity.application.dtos import TeamInvitationOutcome
from agilina_api.identity.application.errors import PasswordPolicyError
from agilina_api.identity.domain.errors import (
    AccountDisabledError,
    AlreadyTeamMemberError,
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationRevokedError,
    UnknownTeamError,
    UserAlreadyExistsError,
)
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import AppUserBuilder, InvitationBuilder, TeamBuilder, next_id
from tests.api.integration.support import stored_invitation, stored_team, stored_user
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


async def test_a_second_valid_invitation_for_the_same_person_revokes_the_first(world, engine):
    team_id = await world.a_team()
    await world.invite(team_id)

    await world.invite(team_id)

    assert await _count(engine, "invitation", "status = 'revoked'") == 1
    assert await _count(engine, "invitation", "status = 'pending'") == 1
    with pytest.raises(InvitationRevokedError):
        await world.activate.handle(ActivateAccount(token=TOKENS[0], password=PASSWORD))


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


# ------------------------------------------------ an admin invites to their team (HU-06) --
async def _atlas_administered_by_diego(session_factory):
    diego = await stored_user(
        session_factory, AppUserBuilder().with_email("diego@example.test").named("Diego")
    )
    team = await stored_team(
        session_factory, TeamBuilder().in_language(Language.ES).with_admin(diego.id)
    )
    return team, diego


async def test_an_admins_invitation_is_authored_by_their_membership_and_activates_in_the_role(
    world, engine, session_factory
):
    team, diego = await _atlas_administered_by_diego(session_factory)
    membership = team.membership_of(diego.id)
    assert membership is not None

    outcome = await world.admin_invites(team.id, diego.id, role=TeamRole.ADMIN)

    assert outcome is TeamInvitationOutcome.INVITATION_SENT
    async with engine.connect() as connection:
        created_by = (await connection.execute(text("SELECT created_by FROM invitation"))).scalar()
    assert created_by == membership.id
    [message] = world.mailer.sent
    assert f"activation_url=https://app.test/activate#t={TOKEN}" in message.text_body
    assert "inviter_name=Diego" in message.text_body and message.subject == "invitation:es"

    activated = await world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))
    assert (activated.team_id, activated.role) == (team.id, TeamRole.ADMIN)


async def test_an_existing_account_joins_without_a_token_and_its_pending_invitation_closes(
    world, engine, session_factory
):
    team, diego = await _atlas_administered_by_diego(session_factory)
    julian = await stored_user(session_factory, AppUserBuilder().with_email("julian@example.test"))
    await stored_invitation(
        session_factory, InvitationBuilder().for_team(team.id).with_unique_token()
    )

    outcome = await world.admin_invites(team.id, diego.id)

    assert outcome is TeamInvitationOutcome.MEMBER_ADDED
    where = f"team_id = '{team.id}' AND user_id = '{julian.id}' AND role = 'member'"
    assert await _count(engine, "team_member", where + " AND status = 'active'") == 1
    assert await _count(engine, "invitation") == 1  # no new invitation, so no token
    assert await _count(engine, "invitation", "status = 'revoked'") == 1
    [message] = world.mailer.sent
    assert message.subject == "member_added:es" and "#t=" not in message.text_body
    assert f"team_url=https://app.test/teams/{team.id}" in message.text_body


async def test_someone_removed_who_is_invited_again_comes_back_with_the_new_role(
    world, engine, session_factory
):
    diego = await stored_user(session_factory, AppUserBuilder().with_unique_email().named("Diego"))
    julian = await stored_user(session_factory, AppUserBuilder().with_email("julian@example.test"))
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(diego.id).with_removed_member(julian.id)
    )

    outcome = await world.admin_invites(team.id, diego.id, role=TeamRole.ADMIN)

    assert outcome is TeamInvitationOutcome.MEMBER_ADDED
    assert await _count(engine, "team_member", f"user_id = '{julian.id}'") == 1  # the same row
    assert (
        await _count(
            engine,
            "team_member",
            f"user_id = '{julian.id}' AND status = 'active' AND role = 'admin'",
        )
        == 1
    )


async def test_inviting_a_current_member_changes_nothing_not_even_their_pending_invitation(
    world, engine, session_factory
):
    team, diego = await _atlas_administered_by_diego(session_factory)
    julian = await stored_user(session_factory, AppUserBuilder().with_email("julian@example.test"))
    await world.admin_invites(team.id, diego.id)  # Julián joins
    world.mailer.sent.clear()
    await stored_invitation(
        session_factory, InvitationBuilder().for_team(team.id).with_unique_token()
    )

    with pytest.raises(AlreadyTeamMemberError):
        await world.admin_invites(team.id, diego.id, role=TeamRole.ADMIN)

    assert world.mailer.sent == []
    assert await _count(engine, "invitation", "status = 'pending'") == 1  # rolled back
    assert await _count(engine, "team_member", f"user_id = '{julian.id}' AND role = 'member'") == 1


async def test_if_the_notice_cannot_be_sent_the_account_does_not_join(
    world, engine, session_factory
):
    team, diego = await _atlas_administered_by_diego(session_factory)
    julian = await stored_user(session_factory, AppUserBuilder().with_email("julian@example.test"))
    world.mailer.fail = True

    with pytest.raises(MailDeliveryError):
        await world.admin_invites(team.id, diego.id)

    assert await _count(engine, "team_member", f"user_id = '{julian.id}'") == 0


async def test_a_disabled_account_is_refused_and_nothing_is_stored(world, engine, session_factory):
    team, diego = await _atlas_administered_by_diego(session_factory)
    await stored_user(
        session_factory, AppUserBuilder().with_email("julian@example.test").disabled()
    )

    with pytest.raises(AccountDisabledError):
        await world.admin_invites(team.id, diego.id)

    assert await _count(engine, "team_member") == 1 and await _count(engine, "invitation") == 0
    assert world.mailer.sent == []


async def test_reinviting_someone_without_account_revokes_the_old_link(world, session_factory):
    team, diego = await _atlas_administered_by_diego(session_factory)
    await world.admin_invites(team.id, diego.id)

    await world.admin_invites(team.id, diego.id)

    with pytest.raises(InvitationRevokedError):
        await world.activate.handle(ActivateAccount(token=TOKENS[0], password=PASSWORD))
    activated = await world.activate.handle(ActivateAccount(token=TOKENS[1], password=PASSWORD))
    assert activated.team_id == team.id
