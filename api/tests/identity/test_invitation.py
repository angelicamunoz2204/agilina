"""The Invitation aggregate: the three states of the link and the seven-day deadline (HU-02)."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from agilina_api.identity.domain.errors import (
    InvalidFullNameError,
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationNotPendingError,
    InvitationRevokedError,
)
from agilina_api.identity.domain.events import InvitationAccepted
from agilina_api.identity.domain.invitation import VALIDITY, Invitation, InvitationStatus
from agilina_api.identity.domain.value_objects import Email, TokenHash
from agilina_shared.enums import TeamRole

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
UTC_MINUS_FIVE = timezone(timedelta(hours=-5))
TOKEN_HASH = TokenHash("a" * 64)


def _issue(**overrides) -> Invitation:
    fields = {
        "invitation_id": uuid4(),
        "team_id": uuid4(),
        "email": Email("julian@example.test"),
        "full_name": "Julián Torres",
        "role": TeamRole.MEMBER,
        "token_hash": TOKEN_HASH,
        "created_by": uuid4(),
        "now": NOW,
    }
    fields.update(overrides)
    return Invitation.issue(**fields)


def _restore(status: InvitationStatus) -> Invitation:
    return Invitation(
        invitation_id=uuid4(),
        team_id=uuid4(),
        email=Email("julian@example.test"),
        full_name="Julián Torres",
        role=TeamRole.MEMBER,
        token_hash=TOKEN_HASH,
        status=status,
        expires_at=NOW + VALIDITY,
        created_by=None,
        created_at=NOW,
    )


# ------------------------------------------------------------------ issuing --
def test_a_new_invitation_is_pending_and_expires_in_seven_days():
    invitation = _issue()

    assert invitation.status is InvitationStatus.PENDING
    assert VALIDITY == timedelta(days=7)
    assert invitation.expires_at == NOW + timedelta(days=7)
    assert invitation.created_at == NOW
    assert invitation.accepted_at is None and invitation.accepted_user_id is None


def test_only_the_hash_of_the_token_is_kept():
    invitation = _issue()

    assert invitation.token_hash == TOKEN_HASH
    assert not hasattr(invitation, "token")


def test_the_operator_can_issue_the_first_invitation_without_a_member_as_author():
    """AD-22: created_by is None when the platform operator issues it."""
    assert _issue(created_by=None).created_by is None


def test_the_name_is_trimmed_and_cannot_be_blank():
    assert _issue(full_name="  Julián Torres  ").full_name == "Julián Torres"
    with pytest.raises(InvalidFullNameError):
        _issue(full_name="   ")


@pytest.mark.parametrize(
    "not_utc",
    [datetime(2026, 10, 4, 12, 0), datetime(2026, 10, 4, 12, 0, tzinfo=UTC_MINUS_FIVE)],
    ids=["naive", "other-offset"],
)
def test_instants_must_be_utc(not_utc: datetime):
    with pytest.raises(ValueError, match="UTC"):
        _issue(now=not_utc)


# -------------------------------------------------- the states of the link --
def test_a_link_is_valid_until_the_exact_moment_it_expires():
    invitation = _issue()
    just_before = invitation.expires_at - timedelta(microseconds=1)

    assert invitation.state_at(NOW) is InvitationStatus.PENDING
    assert invitation.state_at(just_before) is InvitationStatus.PENDING
    assert invitation.state_at(invitation.expires_at) is InvitationStatus.EXPIRED


def test_a_valid_link_can_be_accepted_once_and_records_who_and_when():
    invitation = _issue()
    user_id = uuid4()
    later = NOW + timedelta(days=2)

    invitation.accept(user_id=user_id, now=later)

    assert invitation.status is InvitationStatus.ACCEPTED
    assert invitation.accepted_at == later
    assert invitation.accepted_user_id == user_id


def test_accepting_announces_it_with_an_event_carrying_the_team_role_and_user():
    invitation = _issue(role=TeamRole.ADMIN)
    user_id = uuid4()

    invitation.accept(user_id=user_id, now=NOW)

    [event] = invitation.pull_events()
    assert event == InvitationAccepted(
        occurred_at=NOW,
        invitation_id=invitation.id,
        team_id=invitation.team_id,
        user_id=user_id,
        email=invitation.email,
        role=TeamRole.ADMIN,
    )
    assert invitation.pull_events() == []


def test_a_used_link_cannot_be_used_again():
    invitation = _issue()
    invitation.accept(user_id=uuid4(), now=NOW)
    invitation.pull_events()

    with pytest.raises(InvitationAlreadyUsedError):
        invitation.accept(user_id=uuid4(), now=NOW + timedelta(minutes=1))

    assert invitation.pull_events() == []


def test_an_expired_link_cannot_be_used():
    invitation = _issue()

    with pytest.raises(InvitationExpiredError) as raised:
        invitation.accept(user_id=uuid4(), now=invitation.expires_at)

    assert raised.value.invitation_id == invitation.id
    assert invitation.status is InvitationStatus.PENDING  # a failed attempt changes nothing
    assert invitation.pull_events() == []


def test_a_revoked_invitation_cannot_be_used():
    with pytest.raises(InvitationRevokedError):
        _restore(InvitationStatus.REVOKED).accept(user_id=uuid4(), now=NOW)


def test_the_three_failures_share_a_base_so_a_caller_can_catch_them_together():
    for error in (InvitationAlreadyUsedError, InvitationExpiredError, InvitationRevokedError):
        assert issubclass(error, InvitationNotPendingError)


# ---------------------------------------------------------- storing expiry --
def test_an_overdue_pending_invitation_can_have_its_expiry_stored_once():
    invitation = _issue()
    after = invitation.expires_at + timedelta(seconds=1)

    assert invitation.expire_if_due(after) is True
    assert invitation.status is InvitationStatus.EXPIRED
    assert invitation.expire_if_due(after) is False


def test_expiry_is_not_stored_before_the_deadline_nor_over_a_used_link():
    invitation = _issue()
    assert invitation.expire_if_due(NOW + timedelta(days=6)) is False
    assert invitation.status is InvitationStatus.PENDING

    invitation.accept(user_id=uuid4(), now=NOW)
    assert invitation.expire_if_due(NOW + timedelta(days=30)) is False
    assert invitation.status is InvitationStatus.ACCEPTED
