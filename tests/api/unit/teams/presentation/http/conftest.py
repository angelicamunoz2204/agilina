import pytest

from tests.api.builders import TeamBuilder
from tests.api.unit.teams.presentation.http.support import Api


@pytest.fixture
async def api() -> Api:
    api = Api()
    await (
        TeamBuilder()
        .with_id(api.atlas)
        .with_admin(api.ana)
        .with_member(api.carla)
        .saved_in(api.members_uow.teams)
    )
    return api
