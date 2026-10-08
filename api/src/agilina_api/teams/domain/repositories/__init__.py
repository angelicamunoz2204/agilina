"""Repository interfaces of the teams domain: one per aggregate, in its language.

Implementations live in ``infrastructure``; the domain only states what it needs.
"""

from agilina_api.teams.domain.repositories.sprint_repository import SprintRepository
from agilina_api.teams.domain.repositories.team_repository import TeamRepository

__all__ = [
    "SprintRepository",
    "TeamRepository",
]
