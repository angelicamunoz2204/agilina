"""RemoveMember: an admin takes a person out of the team; its only admin cannot leave, and a
sprint in progress does not prevent it (HU-06)."""

import logging

import pytest

from agilina_api.teams.application.commands.remove_member import RemoveMemberHandler
from agilina_api.teams.domain.errors import LastAdminError, MemberNotFoundError, TeamNotFoundError
from agilina_api.teams.domain.team import MembershipStatus
from tests.api.builders import NOW, RemoveMemberBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeActiveSprints, FakeClock, FakeTeamsUnitOfWork


class Scenario:
    """Ana is the only admin of Atlas and Bruno one of its members."""

    def __init__(self) -> None:
        self.ana, self.bruno = next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = RemoveMemberHandler(lambda: self.uow, FakeClock())

    async def a_team(self, builder: TeamBuilder | None = None):
        team = builder or TeamBuilder().with_admin(self.ana).with_member(self.bruno)
        return await team.saved_in(self.uow.teams)

    def membership(self, team_id, user_id):
        membership = self.uow.teams.teams[team_id].membership_of(user_id)
        assert membership is not None
        return membership


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


async def test_removing_a_member_ends_the_membership_and_commits(scenario):
    team = await scenario.a_team()

    await scenario.handler.handle(
        RemoveMemberBuilder().for_team(team.id).of_user(scenario.bruno).build()
    )

    removed = scenario.membership(team.id, scenario.bruno)
    assert removed.status is MembershipStatus.REMOVED and removed.removed_at == NOW
    assert scenario.uow.teams.saved == [team.id] and scenario.uow.committed is True


async def test_an_admin_can_leave_when_another_admin_stays(scenario):
    team = await scenario.a_team(TeamBuilder().with_admin(scenario.ana).with_admin(scenario.bruno))

    await scenario.handler.handle(
        RemoveMemberBuilder().for_team(team.id).of_user(scenario.ana).build()
    )

    assert not scenario.membership(team.id, scenario.ana).is_active
    assert scenario.uow.teams.teams[team.id].admin_count == 1


async def test_the_only_admin_cannot_be_removed_and_nothing_is_saved(scenario):
    team = await scenario.a_team()

    with pytest.raises(LastAdminError):
        await scenario.handler.handle(
            RemoveMemberBuilder().for_team(team.id).of_user(scenario.ana).build()
        )

    assert scenario.membership(team.id, scenario.ana).is_active
    assert scenario.uow.teams.saved == [] and scenario.uow.committed is False


async def test_a_sprint_in_progress_does_not_prevent_a_removal(scenario):
    team = await scenario.a_team()
    scenario.uow.active_sprints = FakeActiveSprints({team.id})

    await scenario.handler.handle(
        RemoveMemberBuilder().for_team(team.id).of_user(scenario.bruno).build()
    )

    assert not scenario.membership(team.id, scenario.bruno).is_active
    assert scenario.uow.committed is True


async def test_someone_who_is_not_a_member_is_not_found(scenario):
    team = await scenario.a_team()

    with pytest.raises(MemberNotFoundError):
        await scenario.handler.handle(
            RemoveMemberBuilder().for_team(team.id).of_user(next_id()).build()
        )

    assert scenario.uow.committed is False


async def test_a_team_that_does_not_exist_is_not_found(scenario):
    with pytest.raises(TeamNotFoundError):
        await scenario.handler.handle(RemoveMemberBuilder().build())

    assert scenario.uow.committed is False


async def test_a_removal_is_logged_with_who_asked_for_whom_and_the_role_they_had(scenario, caplog):
    team = await scenario.a_team()

    with caplog.at_level(logging.INFO):
        await scenario.handler.handle(
            RemoveMemberBuilder()
            .for_team(team.id)
            .of_user(scenario.bruno)
            .requested_by_admin(scenario.ana)
            .build()
        )

    assert (
        f"Team {team.id}: user {scenario.ana} removed user {scenario.bruno}, who was member"
    ) in caplog.text


async def test_a_refused_removal_logs_nothing(scenario, caplog):
    team = await scenario.a_team()

    with caplog.at_level(logging.INFO), pytest.raises(LastAdminError):
        await scenario.handler.handle(
            RemoveMemberBuilder().for_team(team.id).of_user(scenario.ana).build()
        )

    assert "removed user" not in caplog.text
