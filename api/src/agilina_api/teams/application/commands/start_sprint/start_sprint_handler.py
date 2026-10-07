from collections.abc import Callable
from uuid import UUID, uuid4

from agilina_api.teams.application.commands.start_sprint.start_sprint import StartSprint
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_api.teams.domain.sprint import DailyTime, Sprint, SprintPeriod


class StartSprintHandler:
    """It does not check who asks: the route lets only the team's admins get here.

    The team is loaded first, which locks its row until the transaction ends (the same lock
    every change to its members takes), so starting a sprint and removing a member never
    interleave. The sprint is stored ``active`` in one transaction with its participants. It
    returns only the new sprint's id (CQRS).
    """

    def __init__(
        self,
        uow_factory: Callable[[], TeamsUnitOfWork],
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._uow_factory = uow_factory
        self._new_id = new_id

    async def handle(self, command: StartSprint) -> UUID:
        async with self._uow_factory() as uow:
            team = await uow.teams.get(command.team_id)
            if team is None:
                raise TeamNotFoundError(f"Team {command.team_id} does not exist")
            sprint = Sprint.start(
                sprint_id=self._new_id(),
                team_id=team.id,
                period=SprintPeriod(start=command.start_date, end=command.end_date),
                daily_time=DailyTime(at=command.daily_time, time_zone=command.time_zone),
                participants=command.participants,
            )
            await uow.sprints.add(sprint)
            await uow.commit()
        return sprint.id
