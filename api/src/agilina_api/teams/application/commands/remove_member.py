"""An admin takes a person out of the team (HU-06)."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.ports.outbound import TeamsUnitOfWork
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_api.teams.domain.events import MemberRemovedFromTeam

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoveMember:
    team_id: UUID
    user_id: UUID
    """The member who leaves the team (it may be the admin who asks)."""
    requested_by: UUID
    """The admin who asks: the audit log names them."""


class RemoveMemberHandler:
    """Only the membership ends: the person's account is identity's and is left as it is.
    It does not check who asks: the route lets only the team's admins get here. Once
    committed, the removal is logged with who asked, for whom and the role they had."""

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
