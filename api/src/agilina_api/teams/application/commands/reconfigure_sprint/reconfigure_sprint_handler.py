import logging
from collections.abc import Callable

from agilina_api.teams.application.commands.reconfigure_sprint.reconfigure_sprint import (
    ReconfigureSprint,
)
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import NoActiveSprintError, TeamNotFoundError
from agilina_api.teams.domain.sprint import DailyTime, SprintPeriod

logger = logging.getLogger(__name__)


class ReconfigureSprintHandler:
    """It does not check who asks: the route lets only the team's admins get here.

    Like ``StartSprint``, it loads (and locks) the team first and changes the sprint inside
    that transaction, with the participants checked against the team's active members. Only
    the active sprint is edited; a team without one gets ``NoActiveSprintError`` and nothing
    is saved.

    Once committed, the change is logged with who asked.
    """

    def __init__(self, uow_factory: Callable[[], TeamsUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: ReconfigureSprint) -> None:
        async with self._uow_factory() as uow:
            team = await uow.teams.get(command.team_id)
            if team is None:
                raise TeamNotFoundError(f"Team {command.team_id} does not exist")
            sprint = await uow.sprints.get_active(team.id)
            if sprint is None:
                raise NoActiveSprintError(f"Team {command.team_id} has no active sprint")
            sprint.reconfigure(
                period=SprintPeriod(start=command.start_date, end=command.end_date),
                daily_time=DailyTime(at=command.daily_time, time_zone=command.time_zone),
                participants=command.participants,
                active_members=team.active_member_ids,
            )
            await uow.sprints.save(sprint)
            await uow.commit()
        logger.info(
            "Team %s: user %s reconfigured sprint %s", team.id, command.requested_by, sprint.id
        )
