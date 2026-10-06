"""ListTeamMembers: the team's members with their name, email, role and label, and why a
change is blocked, so the settings screen computes no rule (HU-06)."""

from agilina_api.teams.application.dtos import MemberContact, MemberRecord, MemberView, RoleOption
from agilina_api.teams.application.queries.list_team_members import (
    ListTeamMembers,
    ListTeamMembersHandler,
)
from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_shared.enums import TeamRole
from tests.api.builders import NOW, next_id
from tests.api.doubles import FakeMemberContacts, FakeTeamQueries


class Scenario:
    """Atlas has Ana (admin), bruno (member) and Carla (member), stored in the order they
    joined; their names and emails come from identity."""

    def __init__(self) -> None:
        self.team_id = next_id()
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.queries = FakeTeamQueries(
            members={
                self.team_id: (
                    MemberRecord(user_id=self.carla, role=TeamRole.MEMBER, joined_at=NOW),
                    MemberRecord(user_id=self.ana, role=TeamRole.ADMIN, joined_at=NOW),
                    MemberRecord(user_id=self.bruno, role=TeamRole.MEMBER, joined_at=NOW),
                )
            }
        )
        self.contacts = FakeMemberContacts(
            {
                self.ana: MemberContact(full_name="Ana Gil", email="ana@example.test"),
                self.bruno: MemberContact(full_name="bruno Díaz", email="bruno@example.test"),
                self.carla: MemberContact(full_name="Carla Ruiz", email="carla@example.test"),
            }
        )

    async def list(self, team_id=None):
        handler = ListTeamMembersHandler(self.queries, self.contacts)
        return await handler.handle(ListTeamMembers(team_id=team_id or self.team_id))


async def test_each_member_comes_with_name_email_role_and_label_ordered_by_name():
    scenario = Scenario()

    members = (await scenario.list()).members

    assert members == (
        MemberView(
            user_id=scenario.ana,
            full_name="Ana Gil",
            email="ana@example.test",
            role=TeamRole.ADMIN,
            label="admin",
            role_change_blocked_by=MemberChangeBlocker.LAST_ADMIN,
            removal_blocked_by=MemberChangeBlocker.LAST_ADMIN,
        ),
        MemberView(
            user_id=scenario.bruno,
            full_name="bruno Díaz",
            email="bruno@example.test",
            role=TeamRole.MEMBER,
            label="member",
            role_change_blocked_by=None,
            removal_blocked_by=None,
        ),
        MemberView(
            user_id=scenario.carla,
            full_name="Carla Ruiz",
            email="carla@example.test",
            role=TeamRole.MEMBER,
            label="member",
            role_change_blocked_by=None,
            removal_blocked_by=None,
        ),
    )


async def test_the_roles_an_admin_can_give_come_with_their_labels():
    """Until HU-04 the label is the code of the internal role."""
    roles = (await Scenario().list()).roles

    assert roles == (
        RoleOption(role=TeamRole.ADMIN, label="admin"),
        RoleOption(role=TeamRole.MEMBER, label="member"),
    )


async def test_two_members_with_the_same_name_are_ordered_by_email():
    scenario = Scenario()
    scenario.contacts.contacts[scenario.carla] = MemberContact(
        full_name="ana gil", email="a-second@example.test"
    )

    members = (await scenario.list()).members

    assert [member.email for member in members] == [
        "a-second@example.test",
        "ana@example.test",
        "bruno@example.test",
    ]


async def test_with_a_sprint_in_progress_no_role_can_change_but_members_can_be_removed():
    scenario = Scenario()
    scenario.queries.teams_with_active_sprint.add(scenario.team_id)

    members = (await scenario.list()).members

    assert {member.role_change_blocked_by for member in members} == {
        MemberChangeBlocker.SPRINT_IN_PROGRESS
    }
    assert [member.removal_blocked_by for member in members] == [
        MemberChangeBlocker.LAST_ADMIN,
        None,
        None,
    ]


async def test_with_two_admins_neither_is_blocked():
    scenario = Scenario()
    scenario.queries.members[scenario.team_id] = (
        MemberRecord(user_id=scenario.ana, role=TeamRole.ADMIN, joined_at=NOW),
        MemberRecord(user_id=scenario.bruno, role=TeamRole.ADMIN, joined_at=NOW),
    )

    members = (await scenario.list()).members

    assert [(m.role_change_blocked_by, m.removal_blocked_by) for m in members] == [
        (None, None),
        (None, None),
    ]


async def test_a_team_without_members_lists_nobody_but_still_the_roles():
    listed = await Scenario().list(team_id=next_id())

    assert listed.members == ()
    assert len(listed.roles) == 2
