"""AddTeamMember: it works inside the caller's transaction and never commits."""

import pytest

from agilina_api.teams.application.commands.add_member import AddTeamMember, AddTeamMemberHandler
from agilina_api.teams.domain.errors import AlreadyMemberError, TeamNotFoundError
from agilina_shared.enums import TeamRole
from tests.api.builders import NOW, TeamBuilder, next_id
from tests.api.doubles import FakeClock, InMemoryTeamRepository


async def test_adding_a_member_saves_the_team_and_leaves_the_commit_to_the_caller():
    teams = InMemoryTeamRepository()
    team = await TeamBuilder().saved_in(teams)
    user_id = next_id()

    await AddTeamMemberHandler(teams, FakeClock()).handle(
        AddTeamMember(team_id=team.id, user_id=user_id, role=TeamRole.ADMIN)
    )

    membership = teams.teams[team.id].membership_of(user_id)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert membership.joined_at == NOW
    assert teams.saved == [team.id]


async def test_adding_a_member_to_an_unknown_team_fails():
    with pytest.raises(TeamNotFoundError):
        await AddTeamMemberHandler(InMemoryTeamRepository(), FakeClock()).handle(
            AddTeamMember(team_id=next_id(), user_id=next_id(), role=TeamRole.MEMBER)
        )


async def test_the_same_person_cannot_be_added_twice():
    teams = InMemoryTeamRepository()
    team = await TeamBuilder().saved_in(teams)
    handler = AddTeamMemberHandler(teams, FakeClock())
    command = AddTeamMember(team_id=team.id, user_id=next_id(), role=TeamRole.MEMBER)
    await handler.handle(command)

    with pytest.raises(AlreadyMemberError):
        await handler.handle(command)
