"""Builder of ``Team``."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Protocol, Self
from uuid import UUID

from agilina_api.teams.domain.team import Team
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders.defaults import NOW, TEAM_NAME
from tests.api.builders.identifiers import next_id


@dataclass(frozen=True)
class TeamBuilder:
    """A team called Atlas, in support mode and English, created by the operator at ``NOW``."""

    team_id: UUID = field(default_factory=next_id)
    name: str = TEAM_NAME
    mode: OperationMode = OperationMode.SUPPORT
    language: Language = Language.EN
    created_by: UUID | None = None
    created_at: datetime = NOW
    members: tuple[tuple[UUID, TeamRole], ...] = ()
    creating_admin: UUID | None = None

    def with_id(self, team_id: UUID) -> Self:
        return replace(self, team_id=team_id)

    def named(self, name: str) -> Self:
        return replace(self, name=name)

    def in_language(self, language: Language) -> Self:
        return replace(self, language=language)

    def in_mode(self, mode: OperationMode) -> Self:
        return replace(self, mode=mode)

    def created_by_user(self, user_id: UUID | None) -> Self:
        return replace(self, created_by=user_id)

    def created_at_instant(self, instant: datetime) -> Self:
        return replace(self, created_at=instant)

    def with_member(self, user_id: UUID, role: TeamRole = TeamRole.MEMBER) -> Self:
        return replace(self, members=(*self.members, (user_id, role)))

    def with_admin(self, user_id: UUID) -> Self:
        return self.with_member(user_id, TeamRole.ADMIN)

    def created_with_admin(self, user_id: UUID) -> Self:
        """Created by ``user_id`` through ``Team.create_with_admin``, who becomes its admin.

        That path always starts in support mode and English, so ``in_mode``,
        ``in_language`` and ``created_by_user`` do not apply to it.
        """
        return replace(self, creating_admin=user_id)

    def build(self) -> Team:
        team = self._create()
        for user_id, role in self.members:
            team.add_member(
                membership_id=next_id(), user_id=user_id, role=role, now=self.created_at
            )
        team.pull_events()
        return team

    def _create(self) -> Team:
        if self.creating_admin is not None:
            return Team.create_with_admin(
                team_id=self.team_id,
                name=self.name,
                user_id=self.creating_admin,
                membership_id=next_id(),
                now=self.created_at,
            )
        return Team.create(
            team_id=self.team_id,
            name=self.name,
            created_by=self.created_by,
            now=self.created_at,
            mode=self.mode,
            language=self.language,
        )

    async def saved_in(self, repository: "TeamStore") -> Team:
        team = self.build()
        await repository.add(team)
        return team


class TeamStore(Protocol):
    async def add(self, team: Team) -> None: ...
