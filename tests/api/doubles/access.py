"""Doubles of the shared access ports: ``AuthenticatedUsers`` and ``TeamAccess``."""

from uuid import UUID

from agilina_shared.enums import TeamRole


class FakeAuthenticatedUsers:
    """Knows the tokens the test gives it, each one resolving to a user; any other token
    does not identify anybody, like an invalid one."""

    def __init__(self, users_by_token: dict[str, UUID] | None = None) -> None:
        self.users_by_token = users_by_token or {}

    async def user_id_for(self, bearer_token: str) -> UUID | None:
        return self.users_by_token.get(bearer_token)


class FakeTeamAccess:
    """Knows the memberships the test gives it, as a role by team and user; any other pair
    is not a member, like a foreign team, a removed member or a team that does not exist."""

    def __init__(self, roles: dict[tuple[UUID, UUID], TeamRole] | None = None) -> None:
        self.roles = roles or {}

    async def role_of(self, *, team_id: UUID, user_id: UUID) -> TeamRole | None:
        return self.roles.get((team_id, user_id))
