"""Read side of teams (CQRS): questions that need no aggregate."""

from typing import Protocol
from uuid import UUID

from agilina_api.shared.application.access import MembershipRef
from agilina_api.teams.application.dtos import (
    TeamMemberRecords,
    TeamSummary,
    TeamView,
    UserTeamView,
)


class TeamQueries(Protocol):
    async def get_summary(self, team_id: UUID) -> TeamSummary | None:
        """The team's name, language and active admins, or ``None`` if it does not exist."""
        ...

    async def list_for_user(self, user_id: UUID) -> tuple[UserTeamView, ...]:
        """The teams where the user is an active member, with their role in each, ordered
        by name ignoring case and then by id; empty when there is none.

        The one query keyed by the user instead of the team: it is how a user finds out
        which tenants they belong to, so the team cannot be known beforehand. It only
        returns the user's own memberships.
        """
        ...

    async def get_team(self, team_id: UUID) -> TeamView | None:
        """The team's name, mode and language, or ``None`` if it does not exist."""
        ...

    async def list_members(self, team_id: UUID) -> TeamMemberRecords:
        """The team's active members with their role, in the order they joined, and whether
        the team has a sprint in progress; no members and no sprint when the team does not
        exist. Removed members are not listed (HU-06)."""
        ...

    async def membership_of(self, *, team_id: UUID, user_id: UUID) -> MembershipRef | None:
        """The user's membership in the team while it is active; ``None`` when they were
        never a member, were removed, or the team does not exist.

        It serves the shared ``TeamAccess`` port: the composition root hands this query to
        the dependency that keeps every route of a team to its members.
        """
        ...
