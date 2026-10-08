from pydantic import BaseModel, Field

from agilina_shared.sprint_calendar import SprintPhase


class SprintDayResponse(BaseModel):
    """Day N of M of the sprint now, in the calendar of the daily's capture time zone."""

    number: int = Field(
        description=(
            f"N: 0 while `{SprintPhase.NOT_STARTED}`, from 1 to M while "
            f"`{SprintPhase.IN_PROGRESS}` and M once `{SprintPhase.FINISHED}`."
        )
    )
    total: int = Field(description="M: the calendar days of the period, both ends included.")
    phase: SprintPhase = Field(
        description=(
            "Where today falls relative to the period. It is computed, not stored: an active "
            "sprint may not have started yet or may be over already."
        )
    )
