from datetime import datetime
from uuid import UUID

from agilina_api.shared_kernel import AggregateRoot
from agilina_api.teams.domain.errors import (
    AlreadyMemberError,
    LastAdminError,
    MemberNotFoundError,
)
from agilina_api.teams.domain.events import (
    MemberJoinedTeam,
    MemberRemovedFromTeam,
    MemberRoleChanged,
)
from agilina_api.teams.domain.member_rules import is_last_admin
from agilina_api.teams.domain.team.membership import Membership
from agilina_api.teams.domain.team.membership_status import MembershipStatus
from agilina_api.teams.domain.team_name import TeamName
from agilina_shared.enums import Language, OperationMode, TeamRole


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
        did, to give a team its first admin (AD-22). The name follows ``TeamName``:
        trimmed, not blank and at most 80 characters, on either path.
        """
        return cls(
            team_id=team_id,
            name=TeamName(name).value,
            mode=mode,
            language=language,
            created_by=created_by,
            created_at=now,
        )

    @classmethod
    def create_with_admin(  # noqa: PLR0913
        cls,
        *,
        team_id: UUID,
        name: str,
        user_id: UUID,
        membership_id: UUID,
        now: datetime,
    ) -> "Team":
        """A team created by a user, who becomes its admin (HU-05).

        It starts in support mode and English, like every new team. Making the creator its
        admin lives here and not in the use case, so no path can create a team this way and
        leave it without one.
        """
        team = cls.create(team_id=team_id, name=name, created_by=user_id, now=now)
        team.add_member(membership_id=membership_id, user_id=user_id, role=TeamRole.ADMIN, now=now)
        return team

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
    def active_member_ids(self) -> frozenset[UUID]:
        """The ``app_user`` ids of the team's active members: who may take part in its
        ceremonies (HU-07). Removed members keep their membership, but are not here."""
        return frozenset(m.user_id for m in self._memberships.values() if m.is_active)

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

    def change_member_role(self, *, user_id: UUID, role: TeamRole, now: datetime) -> None:
        """Give an active member another role (HU-06). The same role changes nothing.

        The team's only admin cannot be demoted, also when they ask it themselves: the team
        would be left without an admin.
        """
        membership = self._active_membership(user_id)
        previous = membership.role
        if previous is role:
            return
        self._ensure_not_last_admin(membership)
        membership.change_role(role)
        self._record(
            MemberRoleChanged(
                occurred_at=now, team_id=self.id, user_id=user_id, previous_role=previous, role=role
            )
        )

    def remove_member(self, *, user_id: UUID, now: datetime) -> None:
        """Take an active member out of the team (HU-06). Only the membership ends: the
        person's account belongs to identity and may be in other teams.

        The team's only admin cannot be removed, also when they ask it themselves.
        """
        membership = self._active_membership(user_id)
        self._ensure_not_last_admin(membership)
        membership.remove(now)
        self._record(
            MemberRemovedFromTeam(
                occurred_at=now, team_id=self.id, user_id=user_id, role=membership.role
            )
        )

    def _ensure_not_last_admin(self, membership: Membership) -> None:
        if is_last_admin(membership.role, self.admin_count):
            raise LastAdminError(f"User {membership.user_id} is the only admin of team {self.id}")

    def _active_membership(self, user_id: UUID) -> Membership:
        membership = self._memberships.get(user_id)
        if membership is None or not membership.is_active:
            raise MemberNotFoundError(f"User {user_id} is not an active member of team {self.id}")
        return membership
