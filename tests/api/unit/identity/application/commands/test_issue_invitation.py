"""IssueInvitation: a valid invitation is stored (hash only) and its link is e-mailed."""

from dataclasses import replace
from datetime import timedelta

import pytest

from agilina_api.identity.application.commands.issue_invitation import IssueInvitationHandler
from agilina_api.identity.domain.errors import InvalidEmailError, InvalidFullNameError
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import NOW, TOKEN, IssueInvitationBuilder
from tests.api.doubles import (
    FakeClock,
    FakeIdentityUnitOfWork,
    FakeMailer,
    FakeRenderer,
    FakeTokenGenerator,
)


def _invitation() -> IssueInvitationBuilder:
    """An admin invited with a mixed-case address, to prove it is normalized."""
    return IssueInvitationBuilder().as_admin().with_email("Julian@Example.test")


def _handler(uow: FakeIdentityUnitOfWork, mailer: FakeMailer, clock: FakeClock | None = None):
    return IssueInvitationHandler(
        uow.factory(),
        FakeTokenGenerator(TOKEN),
        FakeRenderer(),
        mailer,
        clock or FakeClock(),
        activation_url="https://app.example.test/activate",
    )


async def test_the_invitation_is_stored_pending_for_seven_days_and_committed():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()

    issued = await _handler(uow, mailer).handle(_invitation().build())

    stored = uow.invitations.by_id[issued.invitation_id]
    assert stored.status is InvitationStatus.PENDING
    assert stored.role is TeamRole.ADMIN and stored.email.value == "julian@example.test"
    assert stored.expires_at == NOW + timedelta(days=7) == issued.expires_at
    assert uow.commits == 1


async def test_only_the_hash_is_stored_never_the_token():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    await _handler(uow, mailer).handle(_invitation().build())

    [stored] = uow.invitations.by_id.values()

    assert stored.token_hash.value != TOKEN
    assert TOKEN not in repr(vars(stored))


async def test_the_link_travels_in_the_email_inside_the_url_fragment():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    await _handler(uow, mailer).handle(_invitation().signed_by("Diego").build())

    [message] = mailer.sent

    assert message.to == "julian@example.test"
    assert "activation_url=https://app.example.test/activate#t=" + TOKEN in message.text_body
    assert "name=Julián Torres" in message.text_body and "team_name=Atlas" in message.text_body
    assert "inviter_name=Diego" in message.text_body
    assert "expires_on=2026-10-11" in message.text_body
    assert message.html_body is not None


async def test_the_email_is_written_in_the_requested_language():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    await _handler(uow, mailer).handle(_invitation().in_language(Language.EN).build())

    assert mailer.sent[0].subject == "invitation:en"


async def test_if_the_email_cannot_be_sent_nothing_is_committed():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    mailer.fail = True

    with pytest.raises(MailDeliveryError):
        await _handler(uow, mailer).handle(_invitation().build())

    assert uow.commits == 0


async def test_a_second_invitation_while_the_first_still_works_revokes_the_first():
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    handler = _handler(uow, mailer)
    invitation = _invitation()  # the same team both times
    first = await handler.handle(invitation.build())

    second = await handler.handle(invitation.with_email("julian@example.test").build())

    assert uow.invitations.by_id[first.invitation_id].status is InvitationStatus.REVOKED
    assert uow.invitations.by_id[second.invitation_id].status is InvitationStatus.PENDING
    assert (first.revoked_previous, second.revoked_previous) == (False, True)
    assert len(mailer.sent) == 2 and uow.commits == 2


async def test_after_the_first_one_expired_a_new_invitation_is_issued_and_the_old_one_is_closed():
    uow, mailer, clock = FakeIdentityUnitOfWork(), FakeMailer(), FakeClock()
    handler = _handler(uow, mailer, clock)
    command = _invitation().build()
    first = await handler.handle(command)
    clock.advance(days=8)

    second = await handler.handle(command)

    assert uow.invitations.by_id[first.invitation_id].status is InvitationStatus.EXPIRED
    assert uow.invitations.by_id[second.invitation_id].status is InvitationStatus.PENDING
    assert len(mailer.sent) == 2


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [("email", "not-an-email", InvalidEmailError), ("full_name", "  ", InvalidFullNameError)],
)
async def test_invalid_data_is_refused_before_anything_is_sent(field, value, error):
    uow, mailer = FakeIdentityUnitOfWork(), FakeMailer()
    command = replace(_invitation().build(), **{field: value})

    with pytest.raises(error):
        await _handler(uow, mailer).handle(command)

    assert mailer.sent == [] and uow.commits == 0
