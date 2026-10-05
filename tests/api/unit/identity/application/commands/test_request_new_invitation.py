"""RequestNewInvitation: the person whose link failed asks the admins for another one."""

import pytest

from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.errors import (
    InvitationNotFoundError,
    InvitationStillValidError,
    NoAdminsToNotifyError,
)
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_shared.enums import Language
from tests.api.builders import (
    ContactBuilder,
    InvitationBuilder,
    RequestNewInvitationBuilder,
    TeamContactsBuilder,
    next_id,
)
from tests.api.doubles import (
    FakeClock,
    FakeIdentityUnitOfWork,
    FakeMailer,
    FakeRenderer,
    FakeTeamContactsDirectory,
)

DIEGO = ContactBuilder().with_email("diego@example.test").named("Diego").build()
LAURA = ContactBuilder().with_email("laura@example.test").named("Laura").build()


async def _setup(
    team: TeamContactsBuilder | None = None, invitation: InvitationBuilder | None = None
):
    """A team with two admins, a pending invitation for it, and the handler."""
    uow, mailer, clock = FakeIdentityUnitOfWork(), FakeMailer(), FakeClock()
    invitation_stored = await (invitation or InvitationBuilder()).saved_in(uow.invitations)
    team_contacts = (team or TeamContactsBuilder().with_admins(DIEGO, LAURA)).build()
    directory = FakeTeamContactsDirectory({invitation_stored.team_id: team_contacts})
    handler = RequestNewInvitationHandler(uow.factory(), directory, FakeRenderer(), mailer, clock)
    return handler, mailer, clock, invitation_stored


async def test_every_admin_is_told_who_needs_a_new_invitation_and_why():
    handler, mailer, clock, _ = await _setup()
    clock.advance(days=8)

    await handler.handle(RequestNewInvitationBuilder().build())

    assert [m.to for m in mailer.sent] == ["diego@example.test", "laura@example.test"]
    body = mailer.sent[0].text_body
    for expected in (
        "requester_email=julian@example.test",
        "requester_name=Julián Torres",
        "team_name=Atlas",
        "reason=expired",
        "admin_name=Diego",
    ):
        assert expected in body


async def test_the_admins_are_written_in_the_team_language():
    handler, mailer, clock, _ = await _setup(
        TeamContactsBuilder().with_admins(DIEGO, LAURA).in_language(Language.EN)
    )
    clock.advance(days=8)

    await handler.handle(RequestNewInvitationBuilder().build())

    assert mailer.sent[0].subject == "new_invitation_request:en"


async def test_a_used_link_also_reaches_the_admins_with_that_reason():
    handler, mailer, _, _ = await _setup(invitation=InvitationBuilder().accepted_by(next_id()))

    await handler.handle(RequestNewInvitationBuilder().build())

    assert "reason=accepted" in mailer.sent[0].text_body


async def test_while_the_link_still_works_there_is_nothing_to_request():
    handler, mailer, _, _ = await _setup()

    with pytest.raises(InvitationStillValidError):
        await handler.handle(RequestNewInvitationBuilder().build())

    assert mailer.sent == []


@pytest.mark.parametrize("token", ["", "short", "Z" * 43])
async def test_an_altered_or_unknown_link_is_not_found(token):
    handler, mailer, clock, _ = await _setup()
    clock.advance(days=8)

    with pytest.raises(InvitationNotFoundError):
        await handler.handle(RequestNewInvitationBuilder().with_token(token).build())

    assert mailer.sent == []


async def test_a_team_without_admins_cannot_be_notified():
    handler, mailer, clock, _ = await _setup(TeamContactsBuilder().without_admins())
    clock.advance(days=8)

    with pytest.raises(NoAdminsToNotifyError):
        await handler.handle(RequestNewInvitationBuilder().build())


async def test_it_fails_only_when_no_admin_could_be_reached():
    handler, mailer, clock, _ = await _setup()
    clock.advance(days=8)
    mailer.fail = True

    with pytest.raises(MailDeliveryError):
        await handler.handle(RequestNewInvitationBuilder().build())
