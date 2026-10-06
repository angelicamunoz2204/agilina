"""CreateTeamAsAdmin against a real PostgreSQL: the team and its admin are stored together."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from agilina_api.teams.application.commands.create_team_as_admin import (
    CreateTeamAsAdmin,
    CreateTeamAsAdminHandler,
)
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory
from tests.api.builders import NOW, next_id
from tests.api.doubles import FakeClock
from tests.api.integration.support import stored_user

pytestmark = pytest.mark.integration


def _handler(session_factory) -> CreateTeamAsAdminHandler:
    return CreateTeamAsAdminHandler(teams_unit_of_work_factory(session_factory), FakeClock())


async def test_creating_a_team_stores_the_team_and_the_admin_membership_together(
    session_factory, engine
):
    user = await stored_user(session_factory)

    team_id = await _handler(session_factory).handle(
        CreateTeamAsAdmin(name="  Atlas  ", user_id=user.id)
    )

    async with engine.connect() as connection:
        team = (
            await connection.execute(
                text(
                    "SELECT name, mode::text, language::text, created_by, created_at "
                    "FROM team WHERE id = :id"
                ),
                {"id": team_id},
            )
        ).one()
        members = (
            await connection.execute(
                text(
                    "SELECT user_id, role::text, status::text FROM team_member WHERE team_id = :id"
                ),
                {"id": team_id},
            )
        ).all()

    assert tuple(team) == ("Atlas", "support", "en", user.id, NOW)
    assert [tuple(member) for member in members] == [(user.id, "admin", "active")]


async def test_a_creator_that_is_not_a_user_stores_nothing(session_factory, engine):
    with pytest.raises(IntegrityError):
        await _handler(session_factory).handle(CreateTeamAsAdmin(name="Atlas", user_id=next_id()))

    async with engine.connect() as connection:
        assert (await connection.execute(text("SELECT count(*) FROM team"))).scalar_one() == 0
