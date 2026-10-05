"""The ``Team`` aggregate: a team, its configuration and its members.

The team is the tenant of the whole product. Membership lives inside the aggregate
because the rules that matter (nobody joins twice, a team keeps at least one admin) are
about the team as a whole. The label shown for a role is *not* stored: it is derived from
the role and the team's mode in the presentation layer (HU-04).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from agilina_api.shared_kernel import AggregateRoot, Entity
from agilina_api.teams.domain.errors import AlreadyMemberError, InvalidTeamNameError
from agilina_api.teams.domain.events import MemberJoinedTeam
from agilina_shared.enums import Language, OperationMode, TeamRole


class MembershipStatus(StrEnum):
    """The values match the PostgreSQL ``membership_status`` enum."""

    ACTIVE = "active"
    REMOVED = "removed"


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


class Team(AggregateRoot[UUID]):
    def __init__(  # noqa: PLR0913
        self,
        *,
        team_id: UUID,
        name: str,
        mode: OperationMode,
        language: Language,
        created_by: UUID | None,
        created_at: datetime,
        memberships: list[Membership] | None = None,
    ) -> None:
        super().__init__(team_id)
        self._name = name
        self._mode = mode
        self._language = language
        self._created_by = created_by
        self._created_at = created_at
        self._memberships: dict[UUID, Membership] = {m.user_id: m for m in memberships or []}

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        *,
        team_id: UUID,
        name: str,
        created_by: UUID | None,
        now: datetime,
        mode: OperationMode = OperationMode.SUPPORT,
        language: Language = Language.EN,
    ) -> "Team":
        """A new team, in support mode and English by default (as the schema does).

        ``created_by`` is the user who created it, or ``None`` when the platform operator
        did, to give a team its first admin (AD-22).
        """
        clean_name = name.strip()
        if not clean_name:
            raise InvalidTeamNameError("A team's name cannot be blank")
        return cls(
            team_id=team_id,
            name=clean_name,
            mode=mode,
            language=language,
            created_by=created_by,
            created_at=now,
        )

    # ------------------------------------------------------------ read state --
    @property
    def name(self) -> str:
        return self._name

    @property
    def mode(self) -> OperationMode:
        return self._mode

    @property
    def language(self) -> Language:
        return self._language

    @property
    def created_by(self) -> UUID | None:
        return self._created_by

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def memberships(self) -> tuple[Membership, ...]:
        return tuple(self._memberships.values())

    def membership_of(self, user_id: UUID) -> Membership | None:
        return self._memberships.get(user_id)

    @property
    def admin_count(self) -> int:
        return sum(
            1 for m in self._memberships.values() if m.is_active and m.role is TeamRole.ADMIN
        )

    # -------------------------------------------------------------- behavior --
    def add_member(
        self, *, membership_id: UUID, user_id: UUID, role: TeamRole, now: datetime
    ) -> Membership:
        """Bring a person into the team with ``role``.

        Someone who had been removed comes back through the same membership; someone who
        is still active cannot join again.
        """
        existing = self._memberships.get(user_id)
        if existing is not None and existing.is_active:
            raise AlreadyMemberError(f"User {user_id} is already a member of team {self.id}")

        if existing is not None:
            existing.rejoin(role, now)
            membership = existing
        else:
            membership = Membership(
                membership_id=membership_id,
                user_id=user_id,
                role=role,
                status=MembershipStatus.ACTIVE,
                joined_at=now,
            )
            self._memberships[user_id] = membership

        self._record(MemberJoinedTeam(occurred_at=now, team_id=self.id, user_id=user_id, role=role))
        return membership
