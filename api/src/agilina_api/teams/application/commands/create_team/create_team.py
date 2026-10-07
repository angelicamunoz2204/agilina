from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import Language


@dataclass(frozen=True)
class CreateTeam:
    name: str
    language: Language = Language.EN
    created_by: UUID | None = None
    """The user who creates it, or ``None`` when the platform operator does, to give the
    team its first admin (AD-22)."""
