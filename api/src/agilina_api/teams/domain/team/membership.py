from datetime import datetime
from uuid import UUID

from agilina_api.shared_kernel import Entity
from agilina_api.teams.domain.team.membership_status import MembershipStatus
from agilina_shared.enums import TeamRole


class Membership(Entity[UUID]):
    """One person's belonging to the team, with their role."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        membership_id: UUID,
        user_id: UUID,
        role: TeamRole,
        status: MembershipStatus,
        joined_at: datetime,
        removed_at: datetime | None = None,
    ) -> None:
        super().__init__(membership_id)
        self._user_id = user_id
        self._role = role
        self._status = status
        self._joined_at = joined_at
        self._removed_at = removed_at

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def role(self) -> TeamRole:
        return self._role

    @property
    def status(self) -> MembershipStatus:
        return self._status

    @property
    def joined_at(self) -> datetime:
        return self._joined_at

    @property
    def removed_at(self) -> datetime | None:
        return self._removed_at

    @property
    def is_active(self) -> bool:
        return self._status is MembershipStatus.ACTIVE

    def rejoin(self, role: TeamRole, now: datetime) -> None:
        """Someone who had been removed comes back (same row, new role and date)."""
        self._role = role
        self._status = MembershipStatus.ACTIVE
        self._joined_at = now
        self._removed_at = None

    def change_role(self, role: TeamRole) -> None:
        self._role = role

    def remove(self, now: datetime) -> None:
        """The person leaves the team. The row stays (``removed`` with its date), so they
        can come back through ``rejoin``."""
        self._status = MembershipStatus.REMOVED
        self._removed_at = now
