"""The sprint, as far as HU-06 needs it: whether one is in progress.

There is no ``Sprint`` aggregate yet: planning, starting and closing a sprint belong to
HU-07. Teams only asks whether a team has one active (``ActiveSprints``).
"""

from agilina_api.teams.domain.sprint.sprint_status import SprintStatus

__all__ = ["SprintStatus"]
