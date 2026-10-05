"""``TeamName``: the name of a team, trimmed and valid by construction (HU-05)."""

from dataclasses import dataclass
from typing import Final

from agilina_api.teams.domain.errors import InvalidTeamNameError

MAX_LENGTH: Final = 80
"""Measured after trimming, so surrounding spaces never count towards the limit. ``len``
counts code points, the same as PostgreSQL's ``char_length``, which backs the rule with
the ``team_name_max_length`` check."""


@dataclass(frozen=True)
class TeamName:
    """A team's name: trimmed, never blank and at most ``MAX_LENGTH`` characters."""

    value: str

    def __post_init__(self) -> None:
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidTeamNameError("A team's name cannot be blank")
        if len(trimmed) > MAX_LENGTH:
            raise InvalidTeamNameError(
                f"A team's name cannot be longer than {MAX_LENGTH} characters"
            )
        object.__setattr__(self, "value", trimmed)

    def __str__(self) -> str:
        return self.value
