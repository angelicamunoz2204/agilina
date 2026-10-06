"""The Team aggregate: creation rules, who can join, and how an admin changes a member's
role or removes them without leaving the team without an admin (HU-06)."""

from datetime import timedelta
from uuid import UUID

import pytest

from agilina_api.teams.domain.errors import (
    AlreadyMemberError,
    InvalidTeamNameError,
    LastAdminError,
    MemberNotFoundError,
)
from agilina_api.teams.domain.events import (
    MemberJoinedTeam,
    MemberRemovedFromTeam,
    MemberRoleChanged,
)
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
    team.remove_member(user_id=user_id, now=NOW + timedelta(days=1))

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


# ------------------------------------------------- created by a user (HU-05) --
def test_a_team_created_by_a_user_makes_them_its_admin():
    user_id = next_id()

    team = TeamBuilder().created_with_admin(user_id).build()

    membership = team.membership_of(user_id)
    assert membership is not None
    assert membership.role is TeamRole.ADMIN and membership.is_active
    assert membership.joined_at == NOW
    assert team.admin_count == 1 and len(team.memberships) == 1


def test_a_team_created_by_a_user_records_who_created_it():
    user_id = next_id()

    assert TeamBuilder().created_with_admin(user_id).build().created_by == user_id


def test_a_team_created_by_a_user_starts_in_support_mode_and_english():
    team = TeamBuilder().created_with_admin(next_id()).build()

    assert team.mode is OperationMode.SUPPORT
    assert team.language is Language.EN


def test_creating_a_team_with_its_admin_records_member_joined():
    team_id, user_id = next_id(), next_id()

    team = Team.create_with_admin(
        team_id=team_id, name="Atlas", user_id=user_id, membership_id=next_id(), now=NOW
    )

    assert team.pull_events() == [
        MemberJoinedTeam(occurred_at=NOW, team_id=team_id, user_id=user_id, role=TeamRole.ADMIN)
    ]


def test_a_team_created_by_a_user_follows_the_name_rule():
    user_id = next_id()

    assert TeamBuilder().named("  Atlas  ").created_with_admin(user_id).build().name == "Atlas"
    with pytest.raises(InvalidTeamNameError):
        TeamBuilder().named("   ").created_with_admin(user_id).build()
    with pytest.raises(InvalidTeamNameError):
        TeamBuilder().named("x" * 81).created_with_admin(user_id).build()


def test_the_operator_team_also_rejects_names_longer_than_80():
    assert TeamBuilder().named("x" * 80).build().name == "x" * 80
    with pytest.raises(InvalidTeamNameError):
        TeamBuilder().named("x" * 81).build()


# ------------------------------------------------------- changing a role (HU-06) --
LATER = NOW + timedelta(days=3)


def test_an_admin_can_promote_a_member():
    admin, member = next_id(), next_id()
    team = TeamBuilder().with_admin(admin).with_member(member).build()

    team.change_member_role(user_id=member, role=TeamRole.ADMIN, now=LATER)

    membership = team.membership_of(member)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert team.admin_count == 2


def test_an_admin_can_be_demoted_when_the_team_has_another_admin():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_admin(bruno).build()

    team.change_member_role(user_id=bruno, role=TeamRole.MEMBER, now=LATER)

    membership = team.membership_of(bruno)
    assert membership is not None and membership.role is TeamRole.MEMBER
    assert team.admin_count == 1


def test_an_admin_can_demote_themselves_when_the_team_has_another_admin():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_admin(bruno).build()

    team.change_member_role(user_id=ana, role=TeamRole.MEMBER, now=LATER)

    membership = team.membership_of(ana)
    assert membership is not None and membership.role is TeamRole.MEMBER


def test_changing_a_role_announces_it_with_the_previous_and_the_new_role():
    admin, member = next_id(), next_id()
    team = TeamBuilder().with_admin(admin).with_member(member).build()

    team.change_member_role(user_id=member, role=TeamRole.ADMIN, now=LATER)

    assert team.pull_events() == [
        MemberRoleChanged(
            occurred_at=LATER,
            team_id=team.id,
            user_id=member,
            previous_role=TeamRole.MEMBER,
            role=TeamRole.ADMIN,
        )
    ]


def test_giving_the_role_a_member_already_has_changes_nothing():
    admin, member = next_id(), next_id()
    team = TeamBuilder().with_admin(admin).with_member(member).build()

    team.change_member_role(user_id=member, role=TeamRole.MEMBER, now=LATER)
    team.change_member_role(user_id=admin, role=TeamRole.ADMIN, now=LATER)

    assert team.pull_events() == []
    membership = team.membership_of(member)
    assert membership is not None and membership.role is TeamRole.MEMBER


def test_the_only_admin_cannot_be_demoted():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_member(bruno).build()

    with pytest.raises(LastAdminError):
        team.change_member_role(user_id=ana, role=TeamRole.MEMBER, now=LATER)

    membership = team.membership_of(ana)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert team.admin_count == 1 and team.pull_events() == []


def test_the_only_admin_cannot_demote_themselves_even_in_a_team_of_one():
    ana = next_id()
    team = TeamBuilder().created_with_admin(ana).build()

    with pytest.raises(LastAdminError):
        team.change_member_role(user_id=ana, role=TeamRole.MEMBER, now=LATER)

    assert team.admin_count == 1


def test_a_removed_admin_does_not_count_so_the_remaining_one_cannot_be_demoted():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_removed_member(bruno, TeamRole.ADMIN).build()

    with pytest.raises(LastAdminError):
        team.change_member_role(user_id=ana, role=TeamRole.MEMBER, now=LATER)


def test_promoting_a_member_is_never_blocked_by_the_last_admin_rule():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_member(bruno).build()

    team.change_member_role(user_id=bruno, role=TeamRole.ADMIN, now=LATER)

    assert team.admin_count == 2


def test_the_role_of_someone_who_is_not_a_member_cannot_change():
    team = TeamBuilder().with_admin(next_id()).build()

    with pytest.raises(MemberNotFoundError):
        team.change_member_role(user_id=next_id(), role=TeamRole.ADMIN, now=LATER)


def test_the_role_of_a_removed_member_cannot_change():
    bruno = next_id()
    team = TeamBuilder().with_admin(next_id()).with_removed_member(bruno).build()

    with pytest.raises(MemberNotFoundError):
        team.change_member_role(user_id=bruno, role=TeamRole.ADMIN, now=LATER)


# ----------------------------------------------------- removing a member (HU-06) --
def test_removing_a_member_keeps_the_row_as_removed_with_its_date():
    admin, member = next_id(), next_id()
    team = TeamBuilder().with_admin(admin).with_member(member).build()

    team.remove_member(user_id=member, now=LATER)

    membership = team.membership_of(member)
    assert membership is not None
    assert membership.status is MembershipStatus.REMOVED and not membership.is_active
    assert membership.removed_at == LATER
    assert membership.role is TeamRole.MEMBER and membership.joined_at == NOW
    assert len(team.memberships) == 2


def test_removing_a_member_announces_it():
    admin, member = next_id(), next_id()
    team = TeamBuilder().with_admin(admin).with_member(member).build()

    team.remove_member(user_id=member, now=LATER)

    assert team.pull_events() == [
        MemberRemovedFromTeam(
            occurred_at=LATER, team_id=team.id, user_id=member, role=TeamRole.MEMBER
        )
    ]


def test_an_admin_can_be_removed_when_the_team_has_another_admin():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_admin(bruno).build()

    team.remove_member(user_id=bruno, now=LATER)

    assert team.admin_count == 1


def test_an_admin_can_remove_themselves_when_the_team_has_another_admin():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_admin(bruno).build()

    team.remove_member(user_id=ana, now=LATER)

    membership = team.membership_of(ana)
    assert membership is not None and not membership.is_active
    assert team.admin_count == 1


def test_the_only_admin_cannot_be_removed():
    ana, bruno = next_id(), next_id()
    team = TeamBuilder().with_admin(ana).with_member(bruno).build()

    with pytest.raises(LastAdminError):
        team.remove_member(user_id=ana, now=LATER)

    membership = team.membership_of(ana)
    assert membership is not None and membership.is_active
    assert team.pull_events() == []


def test_the_only_admin_cannot_remove_themselves_even_in_a_team_of_one():
    ana = next_id()
    team = TeamBuilder().created_with_admin(ana).build()

    with pytest.raises(LastAdminError):
        team.remove_member(user_id=ana, now=LATER)

    assert team.admin_count == 1


def test_the_builder_cannot_remove_the_only_admin_either():
    with pytest.raises(LastAdminError):
        TeamBuilder().with_removed_member(next_id(), TeamRole.ADMIN).build()


def test_someone_who_is_not_a_member_cannot_be_removed():
    team = TeamBuilder().with_admin(next_id()).build()

    with pytest.raises(MemberNotFoundError):
        team.remove_member(user_id=next_id(), now=LATER)


def test_a_member_cannot_be_removed_twice():
    bruno = next_id()
    team = TeamBuilder().with_admin(next_id()).with_removed_member(bruno).build()

    with pytest.raises(MemberNotFoundError):
        team.remove_member(user_id=bruno, now=LATER)

    membership = team.membership_of(bruno)
    assert membership is not None and membership.removed_at == NOW + timedelta(hours=1)
