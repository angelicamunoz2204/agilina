from collections.abc import Callable
from uuid import UUID, uuid4

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.create_team_as_admin.create_team_as_admin import (
    CreateTeamAsAdmin,
)
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.team import Team


class CreateTeamAsAdminHandler:
    """The team and the creator's admin membership are stored in one transaction: if
    either fails, nothing is left half done. It returns only the new team's id (CQRS)."""

    def __init__(
        self,
        uow_factory: Callable[[], TeamsUnitOfWork],
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._new_id = new_id

    async def handle(self, command: CreateTeamAsAdmin) -> UUID:
        team = Team.create_with_admin(
            team_id=self._new_id(),
            name=command.name,
            user_id=command.user_id,
            membership_id=self._new_id(),
            now=self._clock.now(),
        )
        async with self._uow_factory() as uow:
            await uow.teams.add(team)
            await uow.commit()
        return team.id
