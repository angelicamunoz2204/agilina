"""An admin gives a member of the team another role (HU-06)."""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import RoleChangeDuringActiveSprintError, TeamNotFoundError
from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class ChangeMemberRole:
    team_id: UUID
    user_id: UUID
    """The member whose role changes (it may be the admin who asks)."""
    role: TeamRole


class ChangeMemberRoleHandler:
    """It does not check who asks: the route lets only the team's admins get here.

    The sprint is not part of the ``Team`` aggregate, so the use case asks whether one is in
    progress, inside the same transaction and once the team is loaded (and locked), and
    refuses before touching the aggregate. The aggregate keeps the last-admin rule.
    """

    def __init__(self, uow_factory: Callable[[], TeamsUnitOfWork], clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def handle(self, command: ChangeMemberRole) -> None:
        async with self._uow_factory() as uow:
            team = await uow.teams.get(command.team_id)
            if team is None:
                raise TeamNotFoundError(f"Team {command.team_id} does not exist")
            if await uow.sprints.has_active_sprint(command.team_id):
                raise RoleChangeDuringActiveSprintError(
                    f"Team {command.team_id} has a sprint in progress"
                )
            team.change_member_role(
                user_id=command.user_id, role=command.role, now=self._clock.now()
            )
            await uow.teams.save(team)
            await uow.commit()
