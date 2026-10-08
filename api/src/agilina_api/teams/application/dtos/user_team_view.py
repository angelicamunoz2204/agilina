from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import OperationMode, TeamRole


@dataclass(frozen=True)
class UserTeamView:
    """A team the user is an active member of, with the user's role in it (HU-05)."""

    team_id: UUID
    name: str
    role: TeamRole
    mode: OperationMode
    """The team's mode: with the role it gives the label to show (HU-04)."""
