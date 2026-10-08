import logging
from collections.abc import Callable

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.remove_member.remove_member import RemoveMember
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_api.teams.domain.events import MemberRemovedFromTeam

logger = logging.getLogger(__name__)


class RemoveMemberHandler:
    """Only the membership ends: the person's account is identity's and is left as it is.
    It does not check who asks: the route lets only the team's admins get here.

    A member who leaves also leaves the daily of the team's active sprint, and whoever came
    after them moves one turn forward (HU-07). It happens in the same transaction as the
    removal, under the team's lock, and not as a reaction to ``MemberRemovedFromTeam``:
    events are read after the commit, and the sprint must never keep a removed participant.
    A sprint in progress does not prevent the removal, even if its daily is left with no
    participant.

    Once committed, the removal is logged with who asked, for whom and the role they had.
    """

    def __init__(self, uow_factory: Callable[[], TeamsUnitOfWork], clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def handle(self, command: RemoveMember) -> None:
        async with self._uow_factory() as uow:
            team = await uow.teams.get(command.team_id)
            if team is None:
                raise TeamNotFoundError(f"Team {command.team_id} does not exist")
            team.remove_member(user_id=command.user_id, now=self._clock.now())
            await uow.teams.save(team)
            sprint = await uow.sprints.get_active(team.id)
            if sprint is not None and command.user_id in sprint.participants:
                sprint.withdraw_participant(command.user_id)
                await uow.sprints.save(sprint)
            await uow.commit()
        removals = [
            event for event in team.pull_events() if isinstance(event, MemberRemovedFromTeam)
        ]
        for removal in removals:
            logger.info(
                "Team %s: user %s removed user %s, who was %s",
                removal.team_id,
                command.requested_by,
                removal.user_id,
                removal.role,
            )
