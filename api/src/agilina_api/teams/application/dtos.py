"""Data transfer objects of the teams use cases: plain types, no framework."""

from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import Language


@dataclass(frozen=True)
class TeamSummary:
    team_id: UUID
    name: str
    language: Language
    admin_user_ids: tuple[UUID, ...]
