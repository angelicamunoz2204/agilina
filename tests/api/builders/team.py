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

    def build(self) -> Team:
        team = Team.create(
            team_id=self.team_id,
            name=self.name,
            created_by=self.created_by,
            now=self.created_at,
            mode=self.mode,
            language=self.language,
        )
        for user_id, role in self.members:
            team.add_member(
                membership_id=next_id(), user_id=user_id, role=role, now=self.created_at
            )
        team.pull_events()
        return team

    async def saved_in(self, repository: "TeamStore") -> Team:
        team = self.build()
        await repository.add(team)
        return team


class TeamStore(Protocol):
    async def add(self, team: Team) -> None: ...
