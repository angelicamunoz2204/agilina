"""Doubles of the shared access ports: ``AuthenticatedUsers`` and ``TeamAccess``."""

from uuid import UUID

from agilina_api.shared.application.access import MembershipRef
from agilina_shared.enums import TeamRole
from tests.api.builders.identifiers import next_id


class FakeAuthenticatedUsers:
    """Knows the tokens the test gives it, each one resolving to a user; any other token
    does not identify anybody, like an invalid one."""

    def __init__(self, users_by_token: dict[str, UUID] | None = None) -> None:
        self.users_by_token = users_by_token or {}

    async def user_id_for(self, bearer_token: str) -> UUID | None:
        return self.users_by_token.get(bearer_token)


class FakeTeamAccess:
    """Knows the memberships the test gives it, as a role by team and user; any other pair
    is not a member, like a foreign team, a removed member or a team that does not exist.

    Each membership gets its id from ``next_id()`` the first time it is asked for, and keeps
    it; a test that needs a known one sets it in ``membership_ids``."""

    def __init__(
        self,
        roles: dict[tuple[UUID, UUID], TeamRole] | None = None,
        membership_ids: dict[tuple[UUID, UUID], UUID] | None = None,
    ) -> None:
        self.roles = roles or {}
        self.membership_ids = membership_ids or {}

    async def membership_of(self, *, team_id: UUID, user_id: UUID) -> MembershipRef | None:
        role = self.roles.get((team_id, user_id))
        if role is None:
            return None
        if (team_id, user_id) not in self.membership_ids:
            self.membership_ids[(team_id, user_id)] = next_id()
        return MembershipRef(membership_id=self.membership_ids[(team_id, user_id)], role=role)
