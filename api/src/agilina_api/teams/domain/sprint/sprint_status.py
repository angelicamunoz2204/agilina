from enum import StrEnum


class SprintStatus(StrEnum):
    """The values match the PostgreSQL ``sprint_status`` enum."""

    PLANNED = "planned"
    ACTIVE = "active"
    CLOSED = "closed"
