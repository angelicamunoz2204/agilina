"""ActivateAccount: the three states of the link and everything that can go wrong (HU-02)."""

import pytest

from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    InvitationNotFoundError,
    PasswordPolicyError,
)
from agilina_api.identity.domain.errors import (
    InvitationAlreadyUsedError,
    InvitationExpiredError,
)
from agilina_api.identity.domain.invitation import Invitation, InvitationStatus
from agilina_api.identity.domain.value_objects import Email
from agilina_shared.enums import TeamRole
from tests.api.builders import (
    PASSWORD,
    ActivateAccountBuilder,
    AppUserBuilder,
    InvitationBuilder,
)
from tests.api.doubles import FakeClock, FakeIdentityProvider, FakeIdentityUnitOfWork


async def _setup(invitation: Invitation | None = None):
    """A pending admin invitation stored in memory, and the handler that activates it."""
    uow, provider, clock = FakeIdentityUnitOfWork(), FakeIdentityProvider(), FakeClock()
    invitation = invitation or InvitationBuilder().as_admin().build()
    await uow.invitations.add(invitation)
    handler = ActivateAccountHandler(uow.factory(), provider, clock)
    return uow, provider, clock, handler, invitation


async def test_a_valid_link_creates_the_account_joins_the_team_and_uses_the_invitation():
    uow, provider, clock, handler, invitation = await _setup()
    clock.advance(days=2)

    result = await handler.handle(ActivateAccountBuilder().build())

    assert provider.created == [("julian@example.test", "Julián Torres", PASSWORD)]
    [user] = uow.users.users
    assert user.keycloak_subject == "kc-1" and user.id == result.user_id
    assert uow.team_membership.added == [(invitation.team_id, user.id, TeamRole.ADMIN)]
    stored = uow.invitations.by_id[invitation.id]
    assert stored.status is InvitationStatus.ACCEPTED and stored.accepted_user_id == user.id
    assert uow.commits == 1
    assert (result.team_id, result.role) == (invitation.team_id, TeamRole.ADMIN)
    assert result.email == Email("julian@example.test")


async def test_the_account_gets_the_role_the_inviter_chose():
    uow, _, _, handler, _ = await _setup(InvitationBuilder().as_member().build())

    await handler.handle(ActivateAccountBuilder().build())

    assert uow.team_membership.added[0][2] is TeamRole.MEMBER


@pytest.mark.parametrize("altered", ["", "short", "x" * 44, "not a token at all"])
async def test_an_altered_link_is_not_found_and_nothing_outside_is_touched(altered):
    uow, provider, _, handler, _ = await _setup()

    with pytest.raises(InvitationNotFoundError):
        await handler.handle(ActivateAccountBuilder().with_token(altered).build())

    assert provider.created == [] and uow.commits == 0


async def test_a_well_formed_token_that_matches_no_invitation_is_not_found():
    _, provider, _, handler, _ = await _setup()

    with pytest.raises(InvitationNotFoundError):
        await handler.handle(ActivateAccountBuilder().with_token("Z" * 43).build())

    assert provider.created == []


async def test_a_used_link_cannot_be_used_again_and_creates_nothing():
    uow, provider, _, handler, _ = await _setup()
    await handler.handle(ActivateAccountBuilder().build())

    with pytest.raises(InvitationAlreadyUsedError):
        await handler.handle(ActivateAccountBuilder().build())

    assert len(provider.created) == 1 and len(uow.users.users) == 1 and uow.commits == 1


async def test_an_expired_link_cannot_be_used_and_the_identity_provider_is_not_called():
    uow, provider, clock, handler, _ = await _setup()
    clock.advance(days=7)

    with pytest.raises(InvitationExpiredError):
        await handler.handle(ActivateAccountBuilder().build())

    assert provider.created == [] and uow.users.users == [] and uow.commits == 0


async def test_an_email_that_already_has_an_account_is_reported_before_touching_keycloak():
    uow, provider, _, handler, invitation = await _setup()
    await (
        AppUserBuilder().with_subject("old").with_email(invitation.email.value).saved_in(uow.users)
    )

    with pytest.raises(AccountAlreadyExistsError):
        await handler.handle(ActivateAccountBuilder().build())

    assert provider.created == []
    assert uow.invitations.by_id[invitation.id].status is InvitationStatus.PENDING


async def test_a_password_the_policy_refuses_leaves_the_invitation_untouched():
    uow, provider, _, handler, invitation = await _setup()
    provider.refuse_password("min_length")

    with pytest.raises(PasswordPolicyError) as raised:
        await handler.handle(ActivateAccountBuilder().with_password("short").build())

    assert raised.value.reasons == ("min_length",)
    assert uow.invitations.by_id[invitation.id].status is InvitationStatus.PENDING
    assert uow.users.users == [] and uow.commits == 0 and provider.deleted == []


async def test_after_a_refused_password_the_same_link_still_works_with_a_better_one():
    uow, provider, _, handler, invitation = await _setup()
    provider.refuse_password("min_length")
    with pytest.raises(PasswordPolicyError):
        await handler.handle(ActivateAccountBuilder().with_password("short").build())
    provider.error = None

    await handler.handle(ActivateAccountBuilder().build())

    assert uow.invitations.by_id[invitation.id].status is InvitationStatus.ACCEPTED


async def test_an_identity_that_already_exists_in_keycloak_is_an_existing_account():
    _, provider, _, handler, _ = await _setup()
    provider.already_has_the_account()

    with pytest.raises(AccountAlreadyExistsError):
        await handler.handle(ActivateAccountBuilder().build())


async def test_when_keycloak_is_down_the_invitation_is_not_used():
    uow, provider, _, handler, invitation = await _setup()
    provider.be_down()

    with pytest.raises(IdentityProviderUnavailableError):
        await handler.handle(ActivateAccountBuilder().build())

    assert uow.invitations.by_id[invitation.id].status is InvitationStatus.PENDING
    assert uow.commits == 0


async def test_if_the_database_fails_after_keycloak_created_the_account_it_is_removed():
    uow, provider, _, handler, _ = await _setup()
    uow.fail_on_commit = RuntimeError("the database is gone")

    with pytest.raises(RuntimeError, match="database is gone"):
        await handler.handle(ActivateAccountBuilder().build())

    assert provider.deleted == ["kc-1"]


async def test_if_adding_the_member_fails_the_keycloak_account_is_removed():
    uow, provider, _, handler, _ = await _setup()
    uow.team_membership.fail_with = RuntimeError("team is gone")

    with pytest.raises(RuntimeError, match="team is gone"):
        await handler.handle(ActivateAccountBuilder().build())

    assert provider.deleted == ["kc-1"]


async def test_a_failure_while_undoing_does_not_hide_the_original_error():
    uow, provider, _, handler, _ = await _setup()
    uow.fail_on_commit = RuntimeError("the database is gone")
    provider.delete_error = RuntimeError("keycloak is down too")

    with pytest.raises(RuntimeError, match="database is gone"):
        await handler.handle(ActivateAccountBuilder().build())


async def test_the_password_never_shows_in_the_command_representation():
    assert PASSWORD not in repr(ActivateAccountBuilder().build())
