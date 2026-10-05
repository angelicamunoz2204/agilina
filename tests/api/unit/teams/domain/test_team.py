"""The Team aggregate: creation rules and who can join."""

from datetime import timedelta
from uuid import UUID

import pytest

from agilina_api.teams.domain.errors import AlreadyMemberError, InvalidTeamNameError
from agilina_api.teams.domain.events import MemberJoinedTeam
from agilina_api.teams.domain.team import MembershipStatus, Team
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, TeamBuilder, next_id


def _join(team: Team, role: TeamRole = TeamRole.MEMBER, user_id: UUID | None = None, now=NOW):
    """The action under test: a person joins the team. Returns who joined."""
    user_id = user_id or next_id()
    team.add_member(membership_id=next_id(), user_id=user_id, role=role, now=now)
    return user_id


def test_a_new_team_defaults_to_support_mode_and_english_like_the_schema():
    team = TeamBuilder().build()

    assert team.mode is OperationMode.SUPPORT
    assert team.language is Language.EN
    assert team.memberships == ()
    assert team.created_at == NOW


def test_the_name_is_trimmed_and_cannot_be_blank():
    assert TeamBuilder().named("  Atlas  ").build().name == "Atlas"
    with pytest.raises(InvalidTeamNameError):
        TeamBuilder().named("   ").build()


def test_the_operator_can_create_a_team_without_an_author():
    """AD-22: created_by is None when the platform operator creates it."""
    assert TeamBuilder().created_by_user(None).build().created_by is None


def test_adding_a_member_makes_them_active_with_their_role_and_date():
    team = TeamBuilder().build()
    user_id = _join(team, TeamRole.ADMIN)

    membership = team.membership_of(user_id)

    assert membership is not None
    assert membership.role is TeamRole.ADMIN
    assert membership.status is MembershipStatus.ACTIVE
    assert membership.joined_at == NOW
    assert membership.removed_at is None


def test_joining_announces_it():
    team = TeamBuilder().build()
    user_id = _join(team, TeamRole.ADMIN)

    [event] = team.pull_events()

    assert event == MemberJoinedTeam(
        occurred_at=NOW, team_id=team.id, user_id=user_id, role=TeamRole.ADMIN
    )


def test_an_active_member_cannot_join_twice():
    team = TeamBuilder().build()
    user_id = _join(team)

    with pytest.raises(AlreadyMemberError):
        _join(team, user_id=user_id)

    assert len(team.memberships) == 1


def test_someone_removed_comes_back_through_the_same_membership():
    team = TeamBuilder().build()
    user_id = _join(team, TeamRole.MEMBER)
    membership = team.membership_of(user_id)
    assert membership is not None
    original_id = membership.id
    membership._status = MembershipStatus.REMOVED  # the removal rule arrives with HU-06
    membership._removed_at = NOW + timedelta(days=1)

    later = NOW + timedelta(days=5)
    team.add_member(membership_id=next_id(), user_id=user_id, role=TeamRole.ADMIN, now=later)

    back = team.membership_of(user_id)
    assert back is not None and back.id == original_id
    assert back.is_active and back.role is TeamRole.ADMIN
    assert back.joined_at == later and back.removed_at is None
    assert len(team.memberships) == 1


def test_the_admin_count_only_counts_active_admins():
    team = TeamBuilder().build()
    assert team.admin_count == 0
    _join(team, TeamRole.MEMBER)
    _join(team, TeamRole.ADMIN)
    _join(team, TeamRole.ADMIN)

    assert team.admin_count == 2
