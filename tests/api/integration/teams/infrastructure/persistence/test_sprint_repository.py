"""The sprint repository against a real PostgreSQL: the sprint round-trips with the daily's
time as a UTC instant, its capture time zone and the participants in turn order (HU-07)."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.domain.sprint import DailyTime, SprintPeriod, SprintStatus
from agilina_api.teams.infrastructure.persistence.sprint_repository import (
    SqlAlchemySprintRepository,
)
from tests.api.builders import SprintBuilder, TeamBuilder, next_id
from tests.api.integration.support import stored_sprint, stored_team, stored_user

pytestmark = pytest.mark.integration


class Atlas:
    """Atlas, administered by Ana, with Bruno and Carla as members, all with an account."""

    def __init__(self, team, ana, bruno, carla) -> None:
        self.team, self.ana, self.bruno, self.carla = team, ana, bruno, carla


@pytest.fixture
async def atlas(session_factory) -> Atlas:
    ana, bruno, carla = [await stored_user(session_factory) for _ in range(3)]
    team = await stored_team(
        session_factory,
        TeamBuilder().with_admin(ana.id).with_member(bruno.id).with_member(carla.id),
    )
    return Atlas(team, ana.id, bruno.id, carla.id)


async def _active(session_factory, team_id):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        return await SqlAlchemySprintRepository(uow.session).get_active(team_id)


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


async def test_a_started_sprint_round_trips_with_its_participants_in_turn_order(
    session_factory, atlas
):
    sprint = await stored_sprint(
        session_factory,
        SprintBuilder().for_team(atlas.team).with_participants(atlas.carla, atlas.ana, atlas.bruno),
    )

    loaded = await _active(session_factory, atlas.team.id)

    assert loaded is not None
    assert (loaded.id, loaded.team_id, loaded.status) == (
        sprint.id,
        atlas.team.id,
        SprintStatus.ACTIVE,
    )
    assert loaded.period == SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))
    assert loaded.daily_time == DailyTime(
        at=datetime(2026, 10, 5, 14, 0, tzinfo=UTC), time_zone="America/Bogota"
    )
    assert loaded.participants == (atlas.carla, atlas.ana, atlas.bruno)


async def test_the_daily_time_is_stored_as_an_instant_and_the_turns_from_one(
    session_factory, engine, atlas
):
    """No column holds a local time (DoD): the session's time zone does not change what is
    read, because the column is an instant."""
    sprint = await stored_sprint(
        session_factory,
        SprintBuilder()
        .for_team(atlas.team)
        .with_daily_time(datetime(2026, 10, 4, 23, 0, tzinfo=UTC), "Asia/Tokyo")
        .with_participants(atlas.bruno, atlas.ana),
    )

    async with engine.connect() as connection:
        await connection.execute(text("SET TIME ZONE 'America/Los_Angeles'"))
        stored = (
            await connection.execute(
                text(
                    "SELECT daily_time_utc = '2026-10-04T23:00:00Z'::timestamptz, daily_time_zone "
                    "FROM sprint WHERE id = :id"
                ),
                {"id": sprint.id},
            )
        ).one()
    assert tuple(stored) == (True, "Asia/Tokyo")
    assert await _turns(engine, sprint.id) == [(atlas.bruno, 1), (atlas.ana, 2)]


async def test_a_team_without_an_active_sprint_has_none(session_factory, atlas):
    other = await stored_team(session_factory, TeamBuilder().with_admin(atlas.ana))
    await stored_sprint(session_factory, SprintBuilder().for_team(atlas.team).closed())
    await stored_sprint(session_factory, SprintBuilder().for_team(atlas.team).planned())
    await stored_sprint(session_factory, SprintBuilder().for_team(other))

    assert await _active(session_factory, atlas.team.id) is None
    assert await _active(session_factory, next_id()) is None


async def test_each_team_gets_its_own_sprint_and_participants(session_factory, atlas):
    other = await stored_team(session_factory, TeamBuilder().with_admin(atlas.bruno))
    mine = await stored_sprint(session_factory, SprintBuilder().for_team(atlas.team))
    theirs = await stored_sprint(session_factory, SprintBuilder().for_team(other))

    loaded_mine = await _active(session_factory, atlas.team.id)
    loaded_theirs = await _active(session_factory, other.id)

    assert loaded_mine is not None and loaded_theirs is not None
    assert loaded_mine.id == mine.id and loaded_theirs.id == theirs.id
    assert loaded_mine.participants == (atlas.ana, atlas.bruno, atlas.carla)
    assert loaded_theirs.participants == (atlas.bruno,)


async def test_saving_replaces_the_period_the_daily_time_and_the_participants(
    session_factory, engine, atlas
):
    sprint = await stored_sprint(session_factory, SprintBuilder().for_team(atlas.team))
    tokyo = DailyTime(at=datetime(2026, 10, 11, 23, 0, tzinfo=UTC), time_zone="Asia/Tokyo")
    period = SprintPeriod(start=date(2026, 10, 12), end=date(2026, 10, 23))

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemySprintRepository(uow.session)
        loaded = await repository.get_active(atlas.team.id)
        assert loaded is not None
        loaded.reconfigure(period=period, daily_time=tokyo, participants=[atlas.carla, atlas.ana])
        await repository.save(loaded)
        await uow.commit()

    edited = await _active(session_factory, atlas.team.id)
    assert edited is not None and edited.id == sprint.id
    assert (edited.period, edited.daily_time) == (period, tokyo)
    assert edited.status is SprintStatus.ACTIVE
    assert await _turns(engine, sprint.id) == [(atlas.carla, 1), (atlas.ana, 2)]


async def test_reversing_the_turn_order_does_not_collide_with_the_unique_turns(
    session_factory, engine, atlas
):
    """Each participant takes a turn another one had: rewriting them in place would break
    ``sprint_participant_turn_order_unique`` halfway through."""
    sprint = await stored_sprint(session_factory, SprintBuilder().for_team(atlas.team))

    for order in ([atlas.carla, atlas.bruno, atlas.ana], [atlas.bruno, atlas.ana, atlas.carla]):
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            repository = SqlAlchemySprintRepository(uow.session)
            loaded = await repository.get_active(atlas.team.id)
            assert loaded is not None
            loaded.reconfigure(
                period=loaded.period, daily_time=loaded.daily_time, participants=order
            )
            await repository.save(loaded)
            await uow.commit()

        assert await _turns(engine, sprint.id) == [(user, i) for i, user in enumerate(order, 1)]


async def test_saving_a_sprint_that_was_never_stored_fails(session_factory, atlas):
    never_stored = SprintBuilder().for_team(atlas.team).build()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(LookupError):
            await SqlAlchemySprintRepository(uow.session).save(never_stored)


async def test_the_database_keeps_every_participant_a_member_of_the_sprints_team(
    session_factory, atlas
):
    """Both foreign keys of a participant share its ``team_id``: someone who is a member of
    another team only cannot be called to this team's daily."""
    outsider = await stored_user(session_factory)
    await stored_team(session_factory, TeamBuilder().with_admin(outsider.id))

    with pytest.raises(IntegrityError, match="sprint_participant_member_fk"):
        await stored_sprint(
            session_factory,
            SprintBuilder().for_team(atlas.team).with_participants(atlas.ana, outsider.id),
        )

    assert await _active(session_factory, atlas.team.id) is None
