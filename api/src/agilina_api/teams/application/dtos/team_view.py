from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import Language, OperationMode


@dataclass(frozen=True)
class TeamView:
    """One team as its members see it: its name and how Agilina works in it (HU-05)."""

    team_id: UUID
    name: str
    mode: OperationMode
    language: Language
