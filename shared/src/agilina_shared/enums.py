"""Domain enumerations.

The values are the ones that travel through the API and are stored in the
database (they match the PostgreSQL enum types); the labels shown to the user
are resolved in the presentation layer, which is where the rule that the
Admin is displayed as Scrum Master when the team is in support mode lives.
"""

from enum import StrEnum


class OperationMode(StrEnum):
    """The only difference between the two modes is whether Agilina asks for
    approval before executing an action."""

    SUPPORT = "support"
    AUTONOMOUS = "autonomous"


class TeamRole(StrEnum):
    """Internal roles per team. A person can be a member in one team and an
    admin in another: the role is always resolved against the team of the
    request, and a token claim is never trusted without checking the
    membership."""

    ADMIN = "admin"
    MEMBER = "member"


class Language(StrEnum):
    """Team attribute. Parameterizes the transcription model, the template set,
    the language model instructions, the synthesized voice and the language of
    the summary."""

    ES = "es"
    EN = "en"


class CeremonyType(StrEnum):
    DAILY = "daily"


class CeremonyStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEGRADED = "degraded"
