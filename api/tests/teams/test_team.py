"""The Team aggregate: creation rules and who can join."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from agilina_api.teams.domain.errors import AlreadyMemberError, InvalidTeamNameError
from agilina_api.teams.domain.events import MemberJoinedTeam
from agilina_api.teams.domain.team import MembershipStatus, Team
from agilina_shared.enums import Language, OperationMode, TeamRole

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


def _team(**overrides) -> Team:
    fields = {"team_id": uuid4(), "name": "Atlas", "created_by": None, "now": NOW}
    fields.update(overrides)
    return Team.create(**fields)


def _join(team: Team, role: TeamRole = TeamRole.MEMBER, user_id=None, now=NOW):
    user_id = user_id or uuid4()
    team.add_member(membership_id=uuid4(), user_id=user_id, role=role, now=now)
    return user_id


def test_a_new_team_defaults_to_support_mode_and_english_like_the_schema():
    team = _team()

    assert team.mode is OperationMode.SUPPORT
    assert team.language is Language.EN
    assert team.memberships == ()
    assert team.created_at == NOW


def test_the_name_is_trimmed_and_cannot_be_blank():
    assert _team(name="  Atlas  ").name == "Atlas"
    with pytest.raises(InvalidTeamNameError):
        _team(name="   ")


def test_the_operator_can_create_a_team_without_an_author():
    """AD-22: created_by is None when the platform operator creates it."""
    assert _team(created_by=None).created_by is None


def test_adding_a_member_makes_them_active_with_their_role_and_date():
    team = _team()
    user_id = _join(team, TeamRole.ADMIN)

    membership = team.membership_of(user_id)

    assert membership is not None
    assert membership.role is TeamRole.ADMIN
    assert membership.status is MembershipStatus.ACTIVE
    assert membership.joined_at == NOW
    assert membership.removed_at is None


def test_joining_announces_it():
    team = _team()
    user_id = _join(team, TeamRole.ADMIN)

    [event] = team.pull_events()

    assert event == MemberJoinedTeam(
        occurred_at=NOW, team_id=team.id, user_id=user_id, role=TeamRole.ADMIN
    )


def test_an_active_member_cannot_join_twice():
    team = _team()
    user_id = _join(team)

    with pytest.raises(AlreadyMemberError):
        _join(team, user_id=user_id)

    assert len(team.memberships) == 1


def test_someone_removed_comes_back_through_the_same_membership():
    team = _team()
    user_id = _join(team, TeamRole.MEMBER)
    membership = team.membership_of(user_id)
    assert membership is not None
    original_id = membership.id
    membership._status = MembershipStatus.REMOVED  # the removal rule arrives with HU-06
    membership._removed_at = NOW + timedelta(days=1)

    later = NOW + timedelta(days=5)
    team.add_member(membership_id=uuid4(), user_id=user_id, role=TeamRole.ADMIN, now=later)

    back = team.membership_of(user_id)
    assert back is not None and back.id == original_id
    assert back.is_active and back.role is TeamRole.ADMIN
    assert back.joined_at == later and back.removed_at is None
    assert len(team.memberships) == 1


def test_the_admin_count_only_counts_active_admins():
    team = _team()
    assert team.admin_count == 0
    _join(team, TeamRole.MEMBER)
    _join(team, TeamRole.ADMIN)
    _join(team, TeamRole.ADMIN)

    assert team.admin_count == 2
