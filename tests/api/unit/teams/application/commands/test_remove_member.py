"""RemoveMember: an admin takes a person out of the team; its only admin cannot leave, and a
sprint in progress does not prevent it (HU-06). Whoever leaves also leaves the daily of the
active sprint, in the same transaction, and the turns close up (HU-07)."""

import logging

import pytest

from agilina_api.teams.application.commands.remove_member import RemoveMemberHandler
from agilina_api.teams.domain.errors import LastAdminError, MemberNotFoundError, TeamNotFoundError
from agilina_api.teams.domain.team import MembershipStatus
from tests.api.builders import NOW, RemoveMemberBuilder, SprintBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeActiveSprints, FakeClock, FakeTeamsUnitOfWork


class Scenario:
    """Ana is the only admin of Atlas and Bruno one of its members; Carla joins when the test
    needs a third participant."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = RemoveMemberHandler(lambda: self.uow, FakeClock())

    async def a_team(self, builder: TeamBuilder | None = None):
        team = builder or TeamBuilder().with_admin(self.ana).with_member(self.bruno)
        return await team.saved_in(self.uow.teams)

    async def a_team_of_three(self):
        return await self.a_team(
            TeamBuilder().with_admin(self.ana).with_member(self.bruno).with_member(self.carla)
        )

    async def a_sprint(self, builder: SprintBuilder):
        return await builder.saved_in(self.uow.sprints)

    def participants_of(self, sprint_id):
        return self.uow.sprints.sprints[sprint_id].participants

    async def remove(self, team_id, user_id) -> None:
        await self.handler.handle(RemoveMemberBuilder().for_team(team_id).of_user(user_id).build())

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


# ------------------------------------------------- the daily (HU-07) --
async def test_a_member_who_leaves_leaves_the_daily_and_the_turns_close_up(scenario):
    team = await scenario.a_team_of_three()
    sprint = await scenario.a_sprint(
        SprintBuilder()
        .for_team(team)
        .with_participants(scenario.ana, scenario.bruno, scenario.carla)
    )

    await scenario.remove(team.id, scenario.bruno)

    # Carla had turn 3 and now has turn 2.
    assert scenario.participants_of(sprint.id) == (scenario.ana, scenario.carla)
    assert not scenario.membership(team.id, scenario.bruno).is_active


async def test_the_daily_changes_in_the_same_transaction_as_the_removal(scenario):
    team = await scenario.a_team_of_three()
    sprint = await scenario.a_sprint(
        SprintBuilder().for_team(team).with_participants(scenario.bruno, scenario.ana)
    )

    await scenario.remove(team.id, scenario.bruno)

    assert scenario.uow.teams.saved == [team.id] and scenario.uow.sprints.saved == [sprint.id]
    assert scenario.uow.committed is True


async def test_the_only_participant_may_leave_and_the_daily_is_left_with_none(scenario):
    """Q4: the removal is not blocked by the daily; the admin configures it again later."""
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(
        SprintBuilder().for_team(team).with_participants(scenario.bruno)
    )

    await scenario.remove(team.id, scenario.bruno)

    assert scenario.participants_of(sprint.id) == ()
    assert not scenario.membership(team.id, scenario.bruno).is_active
    assert scenario.uow.committed is True


async def test_a_member_who_was_not_in_the_daily_leaves_the_sprint_as_it_was(scenario):
    team = await scenario.a_team_of_three()
    sprint = await scenario.a_sprint(
        SprintBuilder().for_team(team).with_participants(scenario.carla, scenario.ana)
    )

    await scenario.remove(team.id, scenario.bruno)

    assert scenario.participants_of(sprint.id) == (scenario.carla, scenario.ana)
    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is True


async def test_without_an_active_sprint_only_the_membership_changes(scenario):
    """A closed sprint keeps who took part in it: only the active one's daily is changed."""
    team = await scenario.a_team()
    closed = await scenario.a_sprint(
        SprintBuilder().for_team(team).with_participants(scenario.ana, scenario.bruno).closed()
    )

    await scenario.remove(team.id, scenario.bruno)

    assert scenario.participants_of(closed.id) == (scenario.ana, scenario.bruno)
    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is True


async def test_the_active_sprint_of_another_team_is_not_touched(scenario):
    team = await scenario.a_team()
    theirs = await scenario.a_sprint(
        SprintBuilder().for_team_id(next_id()).with_participants(scenario.bruno)
    )

    await scenario.remove(team.id, scenario.bruno)

    assert scenario.participants_of(theirs.id) == (scenario.bruno,)
    assert scenario.uow.sprints.saved == []


async def test_a_refused_removal_leaves_the_daily_as_it_was(scenario):
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(
        SprintBuilder().for_team(team).with_participants(scenario.ana, scenario.bruno)
    )

    with pytest.raises(LastAdminError):
        await scenario.remove(team.id, scenario.ana)

    assert scenario.participants_of(sprint.id) == (scenario.ana, scenario.bruno)
    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is False
