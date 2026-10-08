"""RemoveMember against a real PostgreSQL: whoever leaves the team also leaves the daily of
its active sprint, in the same transaction, and the ones after them move one turn forward
(HU-07)."""

import pytest
from sqlalchemy import text

from tests.api.builders import RemoveMemberBuilder, SprintBuilder, TeamBuilder
from tests.api.integration.support import stored_sprint, stored_team, stored_user
from tests.api.integration.world import World

pytestmark = pytest.mark.integration


class Atlas:
    """Atlas, administered by Ana, with Bruno and Dora as members, all with an account."""

    def __init__(self, world: World, team, ana, bruno, dora) -> None:
        self.world, self.team = world, team
        self.ana, self.bruno, self.dora = ana, bruno, dora

    async def remove(self, user_id) -> None:
        await self.world.remove.handle(
            RemoveMemberBuilder()
            .for_team(self.team.id)
            .of_user(user_id)
            .requested_by_admin(self.ana)
            .build()
        )


@pytest.fixture
async def atlas(session_factory) -> Atlas:
    ana, bruno, dora = [await stored_user(session_factory) for _ in range(3)]
    team = await stored_team(
        session_factory,
        TeamBuilder().with_admin(ana.id).with_member(bruno.id).with_member(dora.id),
    )
    return Atlas(World(session_factory), team, ana.id, bruno.id, dora.id)


async def _turns(engine, sprint_id) -> list[tuple]:
    async with engine.connect() as connection:
        rows = await connection.execute(
            text(
                "SELECT user_id, turn_order FROM sprint_participant WHERE sprint_id = :id "
                "ORDER BY turn_order"
            ),
            {"id": sprint_id},
        )
        return [tuple(row) for row in rows]


async def test_removing_a_participant_compacts_the_turns_in_the_database(
    session_factory, engine, atlas
):
    sprint = await stored_sprint(
        session_factory,
        SprintBuilder().for_team(atlas.team).with_participants(atlas.bruno, atlas.ana, atlas.dora),
    )

    await atlas.remove(atlas.bruno)

    assert await _turns(engine, sprint.id) == [(atlas.ana, 1), (atlas.dora, 2)]


async def test_removing_someone_who_is_not_in_the_daily_leaves_the_turns_as_they_were(
    session_factory, engine, atlas
):
    sprint = await stored_sprint(
        session_factory,
        SprintBuilder().for_team(atlas.team).with_participants(atlas.dora, atlas.ana),
    )

    await atlas.remove(atlas.bruno)

    assert await _turns(engine, sprint.id) == [(atlas.dora, 1), (atlas.ana, 2)]


async def test_removing_the_only_participant_leaves_the_daily_empty(session_factory, engine, atlas):
    sprint = await stored_sprint(
        session_factory, SprintBuilder().for_team(atlas.team).with_participants(atlas.bruno)
    )

    await atlas.remove(atlas.bruno)

    assert await _turns(engine, sprint.id) == []


async def test_a_closed_sprint_keeps_its_daily_as_it_was(session_factory, engine, atlas):
    closed = await stored_sprint(
        session_factory,
        SprintBuilder().for_team(atlas.team).with_participants(atlas.bruno, atlas.ana).closed(),
    )

    await atlas.remove(atlas.bruno)

    assert await _turns(engine, closed.id) == [(atlas.bruno, 1), (atlas.ana, 2)]
