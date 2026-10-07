"""The read side of teams against a real PostgreSQL: the teams of a user, one team, the
membership of a user in it and the members of a team (HU-06)."""

from uuid import UUID

import pytest

from agilina_api.shared.application.access import MembershipRef
from agilina_api.teams.application.dtos import MemberRecord, TeamView, UserTeamView
from agilina_api.teams.domain.team import Team
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, SprintBuilder, TeamBuilder, next_id
from tests.api.integration.support import stored_sprint, stored_team, stored_user

pytestmark = pytest.mark.integration


# --------------------------------------------------------------- list_for_user --
async def test_a_user_with_several_teams_receives_them_all(session_factory):
    ana = await stored_user(session_factory)
    atlas = await stored_team(
        session_factory, TeamBuilder().named("Atlas").created_with_admin(ana.id)
    )
    boreal = await stored_team(session_factory, TeamBuilder().named("Boreal").with_member(ana.id))
    await stored_team(session_factory, TeamBuilder().named("Someone else's"))

    teams = await SqlTeamQueries(session_factory).list_for_user(ana.id)

    assert teams == (
        UserTeamView(team_id=atlas.id, name="Atlas", role=TeamRole.ADMIN),
        UserTeamView(team_id=boreal.id, name="Boreal", role=TeamRole.MEMBER),
    )


async def test_teams_where_the_user_was_removed_are_not_listed(session_factory):
    ana = await stored_user(session_factory)
    kept = await stored_team(session_factory, TeamBuilder().named("Atlas").with_admin(ana.id))
    await stored_team(session_factory, TeamBuilder().named("Boreal").with_removed_member(ana.id))

    teams = await SqlTeamQueries(session_factory).list_for_user(ana.id)

    assert [team.team_id for team in teams] == [kept.id]


async def test_the_list_is_ordered_by_name_ignoring_case(session_factory):
    ana = await stored_user(session_factory)
    for name in ["charlie", "Bravo", "alpha", "Delta"]:
        await stored_team(session_factory, TeamBuilder().named(name).with_member(ana.id))

    teams = await SqlTeamQueries(session_factory).list_for_user(ana.id)

    assert [team.name for team in teams] == ["alpha", "Bravo", "charlie", "Delta"]


async def test_teams_with_the_same_name_are_listed_by_id(session_factory):
    ana = await stored_user(session_factory)
    lower_id, higher_id = next_id(), next_id()
    for team_id in (higher_id, lower_id):  # stored in the opposite order
        await stored_team(
            session_factory, TeamBuilder().with_id(team_id).named("Atlas").with_member(ana.id)
        )

    teams = await SqlTeamQueries(session_factory).list_for_user(ana.id)

    assert [team.team_id for team in teams] == [lower_id, higher_id]


async def test_a_user_without_teams_receives_an_empty_list(session_factory):
    ana = await stored_user(session_factory)
    await stored_team(session_factory)

    assert await SqlTeamQueries(session_factory).list_for_user(ana.id) == ()


# --------------------------------------------------------------- membership_of --
async def test_membership_of_returns_the_stored_membership_of_an_active_member(session_factory):
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(
        session_factory, TeamBuilder().created_with_admin(ana.id).with_member(bruno.id)
    )
    queries = SqlTeamQueries(session_factory)

    of_ana = await queries.membership_of(team_id=team.id, user_id=ana.id)
    of_bruno = await queries.membership_of(team_id=team.id, user_id=bruno.id)

    assert of_ana == MembershipRef(membership_id=_membership_id(team, ana.id), role=TeamRole.ADMIN)
    assert of_bruno == MembershipRef(
        membership_id=_membership_id(team, bruno.id), role=TeamRole.MEMBER
    )


async def test_membership_of_ignores_removed_members(session_factory):
    ana = await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().with_removed_member(ana.id))

    queries = SqlTeamQueries(session_factory)
    assert await queries.membership_of(team_id=team.id, user_id=ana.id) is None


async def test_membership_of_is_none_for_another_team(session_factory):
    ana = await stored_user(session_factory)
    await stored_team(session_factory, TeamBuilder().created_with_admin(ana.id))
    other = await stored_team(session_factory)
    queries = SqlTeamQueries(session_factory)

    assert await queries.membership_of(team_id=other.id, user_id=ana.id) is None
    assert await queries.membership_of(team_id=next_id(), user_id=ana.id) is None


def _membership_id(team: Team, user_id: UUID) -> UUID:
    membership = team.membership_of(user_id)
    assert membership is not None
    return membership.id


# -------------------------------------------------------------------- get_team --
async def test_get_team_returns_mode_and_language(session_factory):
    ana = await stored_user(session_factory)
    created = await stored_team(
        session_factory, TeamBuilder().named("Atlas").created_with_admin(ana.id)
    )
    operator = await stored_team(
        session_factory,
        TeamBuilder().named("Boreal").in_language(Language.ES).in_mode(OperationMode.AUTONOMOUS),
    )
    queries = SqlTeamQueries(session_factory)

    assert await queries.get_team(created.id) == TeamView(
        team_id=created.id, name="Atlas", mode=OperationMode.SUPPORT, language=Language.EN
    )
    assert await queries.get_team(operator.id) == TeamView(
        team_id=operator.id, name="Boreal", mode=OperationMode.AUTONOMOUS, language=Language.ES
    )


async def test_get_team_is_none_for_a_team_that_does_not_exist(session_factory):
    assert await SqlTeamQueries(session_factory).get_team(next_id()) is None


# ---------------------------------------------------------------- list_members --
async def test_list_members_returns_the_active_members_with_their_role_in_joining_order(
    session_factory,
):
    carla, ana, bruno = (
        await stored_user(session_factory),
        await stored_user(session_factory),
        await stored_user(session_factory),
    )
    team = await stored_team(
        session_factory,
        TeamBuilder().with_member(carla.id).with_admin(ana.id).with_removed_member(bruno.id),
    )
    await stored_team(session_factory, TeamBuilder().with_admin(bruno.id))  # someone else's

    listed = await SqlTeamQueries(session_factory).list_members(team.id)

    assert listed.members == (
        MemberRecord(user_id=carla.id, role=TeamRole.MEMBER, joined_at=NOW),
        MemberRecord(user_id=ana.id, role=TeamRole.ADMIN, joined_at=NOW),
    )
    assert listed.has_active_sprint is False


async def test_list_members_says_whether_the_team_has_a_sprint_in_progress(session_factory):
    ana = await stored_user(session_factory)
    with_sprint = await stored_team(session_factory, TeamBuilder().with_admin(ana.id))
    with_closed = await stored_team(session_factory, TeamBuilder().with_admin(ana.id))
    await stored_sprint(session_factory, SprintBuilder().for_team(with_sprint))
    await stored_sprint(session_factory, SprintBuilder().for_team(with_closed).closed())
    queries = SqlTeamQueries(session_factory)

    assert (await queries.list_members(with_sprint.id)).has_active_sprint is True
    assert (await queries.list_members(with_closed.id)).has_active_sprint is False


async def test_list_members_of_a_team_that_does_not_exist_is_empty(session_factory):
    listed = await SqlTeamQueries(session_factory).list_members(next_id())

    assert listed.members == () and listed.has_active_sprint is False
