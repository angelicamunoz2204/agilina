from datetime import date
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class SprintRequest(BaseModel):
    """The whole configuration of the sprint, to create it or to edit the active one. The
    team comes from the path.

    The shape is checked here (`422 validation_error`); the rules, by the domain, each with
    its own code: `sprint_ends_before_start`, `invalid_time_zone`, `no_daily_participants`,
    `duplicate_daily_participant` and `daily_participant_not_a_member`."""

    # An unknown field (``team_id``, ``status``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    start_date: date = Field(
        description="The sprint's first day, a calendar date with no time of day.",
        examples=["2026-10-05"],
    )
    end_date: date = Field(
        description=(
            "The sprint's last day, included. Every day of the period counts, weekends too. "
            "It may be the start date, but not before it (`sprint_ends_before_start`)."
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
            "wall-clock time and the sprint's calendar, and replaces the stored one. A key the "
            "time zone database does not know, with its exact case, answers `invalid_time_zone`."
        ),
        examples=["America/Bogota"],
    )
    participants: list[UUID] = Field(
        description=(
            "The `user_id` of the daily's participants, in turn order: the first one speaks "
            "first. At least one (`no_daily_participants`), none twice "
            "(`duplicate_daily_participant`) and each an active member of the team "
            "(`daily_participant_not_a_member`)."
        )
    )
