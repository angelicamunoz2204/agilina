"""GetTeamUser: one active member of a team, with the same data the list gives for them."""

import pytest

from agilina_api.teams.application.dtos import MemberContact, MemberRecord
from agilina_api.teams.application.queries.get_team_user import GetTeamUser, GetTeamUserHandler
from agilina_api.teams.domain.errors import MemberNotFoundError
from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_shared.enums import OperationMode, RoleLabel, TeamRole
from tests.api.builders import NOW, next_id
from tests.api.doubles import FakeMemberContacts, FakeTeamQueries


class Scenario:
    """Atlas has Ana (its only admin) and Carla (a member)."""

    def __init__(self) -> None:
        self.team_id, self.ana, self.carla = next_id(), next_id(), next_id()
        self.queries = FakeTeamQueries(
            members={
                self.team_id: (
                    MemberRecord(user_id=self.ana, role=TeamRole.ADMIN, joined_at=NOW),
                    MemberRecord(user_id=self.carla, role=TeamRole.MEMBER, joined_at=NOW),
                )
            }
        )
        self.contacts = FakeMemberContacts(
            {
                self.ana: MemberContact(full_name="Ana Gil", email="ana@example.test"),
                self.carla: MemberContact(full_name="Carla Ruiz", email="carla@example.test"),
            }
        )

    async def get(self, user_id):
        handler = GetTeamUserHandler(self.queries, self.contacts)
        return await handler.handle(GetTeamUser(team_id=self.team_id, user_id=user_id))


async def test_it_returns_the_name_email_role_label_and_date_of_the_user():
    scenario = Scenario()

    view = await scenario.get(scenario.carla)

    assert (view.full_name, view.email, view.role) == (
        "Carla Ruiz",
        "carla@example.test",
        TeamRole.MEMBER,
    )
    assert view.label is RoleLabel.MEMBER and view.joined_at == NOW


async def test_it_says_why_the_role_cannot_change_with_the_same_rules_as_the_list():
    scenario = Scenario()

    ana = await scenario.get(scenario.ana)

    assert ana.role_change_blocked_by is MemberChangeBlocker.LAST_ADMIN
    assert ana.removal_blocked_by is MemberChangeBlocker.LAST_ADMIN


async def test_a_sprint_in_progress_blocks_the_role_change_first():
    scenario = Scenario()
    scenario.queries.teams_with_active_sprint.add(scenario.team_id)

    carla = await scenario.get(scenario.carla)

    assert carla.role_change_blocked_by is MemberChangeBlocker.SPRINT_IN_PROGRESS
    assert carla.removal_blocked_by is None


@pytest.mark.parametrize(
    ("mode", "label"),
    [(OperationMode.SUPPORT, RoleLabel.SCRUM_MASTER), (OperationMode.AUTONOMOUS, RoleLabel.ADMIN)],
)
async def test_the_label_of_the_admin_follows_the_mode_of_the_team(mode, label):
    scenario = Scenario()
    scenario.queries.modes[scenario.team_id] = mode

    assert (await scenario.get(scenario.ana)).label is label


async def test_someone_who_is_not_an_active_member_is_not_found():
    scenario = Scenario()

    with pytest.raises(MemberNotFoundError):
        await scenario.get(next_id())
