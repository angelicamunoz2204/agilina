from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.bootstrap.context_adapters.teams_backed_membership import TeamsBackedMembership
from agilina_api.identity.application.ports.outbound import TeamMembership
from agilina_api.shared.application.ports import Clock


def team_membership_factory(clock: Clock) -> Callable[[AsyncSession], TeamMembership]:
    return lambda session: TeamsBackedMembership(session, clock)
