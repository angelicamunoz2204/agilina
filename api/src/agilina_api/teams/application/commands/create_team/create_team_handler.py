from collections.abc import Callable
from uuid import UUID, uuid4

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.create_team.create_team import CreateTeam
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.team import Team


class CreateTeamHandler:
    def __init__(
        self,
        uow_factory: Callable[[], TeamsUnitOfWork],
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._new_id = new_id

    async def handle(self, command: CreateTeam) -> UUID:
        team = Team.create(
            team_id=self._new_id(),
            name=command.name,
            created_by=command.created_by,
            now=self._clock.now(),
            language=command.language,
        )
        async with self._uow_factory() as uow:
            await uow.teams.add(team)
            await uow.commit()
        return team.id
