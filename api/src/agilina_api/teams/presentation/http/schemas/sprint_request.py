from datetime import date
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class SprintRequest(BaseModel):
    """The whole configuration of the sprint, to create it or to edit the active one. The
    team comes from the path."""

    # An unknown field (``team_id``, ``status``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    start_date: date = Field(
        description="The sprint's first day, a calendar date with no time of day.",
        examples=["2026-10-05"],
    )
    end_date: date = Field(
        description=(
            "The sprint's last day, included. Every day of the period counts, weekends too."
        ),
        examples=["2026-10-16"],
    )
    daily_time: AwareDatetime = Field(
        description=(
            "The daily's wall-clock time, as the instant it falls on in the capture time zone "
            "on one date of the sprint (the web sends the start date in UTC, `Z`). One time "
            "for the whole team; a value without an offset answers `422 validation_error`."
        ),
        examples=["2026-10-05T14:00:00Z"],
    )
    time_zone: str = Field(
        description=(
            "The IANA time zone of the browser of whoever saves (AD-31). It fixes the daily's "
            "wall-clock time and the sprint's calendar, and replaces the stored one."
        ),
        examples=["America/Bogota"],
    )
    participants: list[UUID] = Field(
        description=(
            "The `user_id` of the daily's participants, in turn order: the first one speaks first."
        )
    )
