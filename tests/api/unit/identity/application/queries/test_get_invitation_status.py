"""GetInvitationStatus: what the activation page asks about a link."""

import pytest

from agilina_api.identity.application.errors import InvitationNotFoundError
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatus,
    GetInvitationStatusHandler,
)
from agilina_api.identity.domain.invitation import InvitationStatus
from tests.api.builders import NOW, TOKEN, InvitationBuilder, next_id
from tests.api.doubles import FakeClock, FakeInvitationQueries, InMemoryInvitationRepository


async def _handler():
    repository, clock = InMemoryInvitationRepository(), FakeClock()
    invitation = await InvitationBuilder().saved_in(repository)
    return (
        GetInvitationStatusHandler(FakeInvitationQueries(repository), clock),
        clock,
        invitation,
        repository,
    )


async def test_a_valid_link_reports_who_it_is_for():
    handler, _, invitation, _ = await _handler()

    view = await handler.handle(GetInvitationStatus(token=TOKEN))

    assert view.email == "julian@example.test" and view.full_name == "Julián Torres"
    assert view.status is InvitationStatus.PENDING and view.expires_at == invitation.expires_at


async def test_a_used_link_reports_accepted_and_an_overdue_one_expired():
    handler, clock, invitation, repository = await _handler()
    clock.advance(days=8)
    assert (
        await handler.handle(GetInvitationStatus(token=TOKEN))
    ).status is InvitationStatus.EXPIRED

    clock.current = NOW
    invitation.accept(user_id=next_id(), now=NOW)
    await repository.save(invitation)
    assert (
        await handler.handle(GetInvitationStatus(token=TOKEN))
    ).status is InvitationStatus.ACCEPTED


@pytest.mark.parametrize("token", ["", "short", "Z" * 43])
async def test_an_altered_or_unknown_link_is_not_found(token):
    handler, _, _, _ = await _handler()

    with pytest.raises(InvitationNotFoundError):
        await handler.handle(GetInvitationStatus(token=token))
