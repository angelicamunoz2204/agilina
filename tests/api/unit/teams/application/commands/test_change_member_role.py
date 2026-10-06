"""ChangeMemberRole: an admin gives a member another role, unless the team has a sprint in
progress or the change would leave it without an admin (HU-06)."""

import pytest

from agilina_api.teams.application.commands.change_member_role import ChangeMemberRoleHandler
from agilina_api.teams.domain.errors import (
    LastAdminError,
    MemberNotFoundError,
    RoleChangeDuringActiveSprintError,
    TeamNotFoundError,
)
from agilina_shared.enums import TeamRole
from tests.api.builders import ChangeMemberRoleBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeActiveSprints, FakeClock, FakeTeamsUnitOfWork


class Scenario:
    """Ana is the only admin of Atlas and Bruno one of its members."""

    def __init__(self) -> None:
        self.ana, self.bruno = next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = ChangeMemberRoleHandler(lambda: self.uow, FakeClock())

    async def a_team(self, builder: TeamBuilder | None = None):
        team = builder or TeamBuilder().with_admin(self.ana).with_member(self.bruno)
        return await team.saved_in(self.uow.teams)

    def role_of(self, team_id, user_id) -> TeamRole:
        membership = self.uow.teams.teams[team_id].membership_of(user_id)
        assert membership is not None
        return membership.role


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


async def test_promoting_a_member_is_saved_and_committed(scenario):
    team = await scenario.a_team()

    await scenario.handler.handle(
        ChangeMemberRoleBuilder().for_team(team.id).of_user(scenario.bruno).build()
    )

    assert scenario.role_of(team.id, scenario.bruno) is TeamRole.ADMIN
    assert scenario.uow.teams.saved == [team.id] and scenario.uow.committed is True


async def test_demoting_one_of_two_admins_is_allowed(scenario):
    team = await scenario.a_team(TeamBuilder().with_admin(scenario.ana).with_admin(scenario.bruno))

    await scenario.handler.handle(
        ChangeMemberRoleBuilder()
        .for_team(team.id)
        .of_user(scenario.ana)
        .to_role(TeamRole.MEMBER)
        .build()
    )

    assert scenario.role_of(team.id, scenario.ana) is TeamRole.MEMBER
    assert scenario.uow.committed is True


async def test_the_only_admin_cannot_be_demoted_and_nothing_is_saved(scenario):
    team = await scenario.a_team()

    with pytest.raises(LastAdminError):
        await scenario.handler.handle(
            ChangeMemberRoleBuilder()
            .for_team(team.id)
            .of_user(scenario.ana)
            .to_role(TeamRole.MEMBER)
            .build()
        )

    assert scenario.role_of(team.id, scenario.ana) is TeamRole.ADMIN
    assert scenario.uow.teams.saved == [] and scenario.uow.committed is False


async def test_with_a_sprint_in_progress_no_role_changes_and_nothing_is_saved(scenario):
    team = await scenario.a_team()
    scenario.uow.sprints = FakeActiveSprints({team.id})

    with pytest.raises(RoleChangeDuringActiveSprintError):
        await scenario.handler.handle(
            ChangeMemberRoleBuilder().for_team(team.id).of_user(scenario.bruno).build()
        )

    assert scenario.role_of(team.id, scenario.bruno) is TeamRole.MEMBER
    assert scenario.uow.teams.saved == [] and scenario.uow.committed is False


async def test_a_sprint_in_progress_in_another_team_does_not_block_the_change(scenario):
    team = await scenario.a_team()
    scenario.uow.sprints = FakeActiveSprints({next_id()})

    await scenario.handler.handle(
        ChangeMemberRoleBuilder().for_team(team.id).of_user(scenario.bruno).build()
    )

    assert scenario.role_of(team.id, scenario.bruno) is TeamRole.ADMIN


async def test_someone_who_is_not_a_member_is_not_found(scenario):
    team = await scenario.a_team()

    with pytest.raises(MemberNotFoundError):
        await scenario.handler.handle(
            ChangeMemberRoleBuilder().for_team(team.id).of_user(next_id()).build()
        )

    assert scenario.uow.committed is False


async def test_a_team_that_does_not_exist_is_not_found(scenario):
    with pytest.raises(TeamNotFoundError):
        await scenario.handler.handle(ChangeMemberRoleBuilder().build())

    assert scenario.uow.committed is False
