from dataclasses import dataclass

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class RoleOption:
    """A role an admin can give, with the label the interface shows for it."""

    role: TeamRole
    label: str
