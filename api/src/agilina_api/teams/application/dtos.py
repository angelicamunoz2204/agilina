"""Data transfer objects of the teams use cases: plain types, no framework."""

from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import Language, OperationMode, TeamRole


@dataclass(frozen=True)
class TeamSummary:
    team_id: UUID
    name: str
    language: Language
    admin_user_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class UserTeamView:
    """A team the user is an active member of, with the user's role in it (HU-05)."""

    team_id: UUID
    name: str
    role: TeamRole


@dataclass(frozen=True)
class TeamView:
    """One team as its members see it: its name and how Agilina works in it (HU-05)."""

    team_id: UUID
    name: str
    mode: OperationMode
    language: Language
