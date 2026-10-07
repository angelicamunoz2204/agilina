from collections.abc import Callable
from uuid import UUID, uuid4

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.add_member.add_team_member import AddTeamMember
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_api.teams.domain.repositories import TeamRepository


class AddTeamMemberHandler:
    """Unlike the other handlers it does **not** own a transaction: it works on the
    repository it is given and leaves the commit to the caller. It exists to be used
    *inside* another context's use case (accepting an invitation adds the member in the
    same transaction), through a port that the composition root implements."""

    def __init__(
        self, teams: TeamRepository, clock: Clock, new_id: Callable[[], UUID] = uuid4
    ) -> None:
        self._teams = teams
        self._clock = clock
        self._new_id = new_id

    async def handle(self, command: AddTeamMember) -> None:
        team = await self._teams.get(command.team_id)
        if team is None:
            raise TeamNotFoundError(f"Team {command.team_id} does not exist")
        team.add_member(
            membership_id=self._new_id(),
            user_id=command.user_id,
            role=command.role,
            now=self._clock.now(),
        )
        await self._teams.save(team)
