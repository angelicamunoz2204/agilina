"""An admin takes a person out of the team (HU-06)."""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import TeamNotFoundError


@dataclass(frozen=True)
class RemoveMember:
    team_id: UUID
    user_id: UUID
    """The member who leaves the team (it may be the admin who asks)."""


class RemoveMemberHandler:
    """Only the membership ends: the person's account is identity's and is left as it is.
    It does not check who asks: the route lets only the team's admins get here."""

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
            await uow.commit()
