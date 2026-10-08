from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class StartSprint:
    team_id: UUID
    start_date: date
    end_date: date
    daily_time: datetime
    """The daily's wall-clock time as an instant with its offset (AD-31)."""
    time_zone: str
    """The IANA time zone of the browser of whoever saves the sprint."""
    participants: tuple[UUID, ...]
    """The ``app_user`` ids of the daily's participants, in turn order."""
    requested_by: UUID
    """The admin who asks: the audit log names them."""
