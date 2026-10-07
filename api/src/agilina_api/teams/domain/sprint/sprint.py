from collections.abc import Sequence
from uuid import UUID

from agilina_api.shared_kernel import AggregateRoot
from agilina_api.teams.domain.sprint.daily_time import DailyTime
from agilina_api.teams.domain.sprint.sprint_period import SprintPeriod
from agilina_api.teams.domain.sprint.sprint_status import SprintStatus


class Sprint(AggregateRoot[UUID]):
    """A team's sprint: its period, the daily's time and who is called to the daily, in turn
    order (HU-07).

    ``participants`` holds the ``app_user`` ids of the daily's participants; the position in
    the tuple is the turn order, so the order goes from 1 to k with no gaps by construction.
    The sprint is not part of the ``Team`` aggregate: the use cases load (and lock) the team
    first and hand the sprint what it needs from it.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        sprint_id: UUID,
        team_id: UUID,
        period: SprintPeriod,
        daily_time: DailyTime,
        participants: Sequence[UUID],
        status: SprintStatus,
    ) -> None:
        super().__init__(sprint_id)
        self._team_id = team_id
        self._period = period
        self._daily_time = daily_time
        self._participants = tuple(participants)
        self._status = status

    @classmethod
    def start(
        cls,
        *,
        sprint_id: UUID,
        team_id: UUID,
        period: SprintPeriod,
        daily_time: DailyTime,
        participants: Sequence[UUID],
    ) -> "Sprint":
        """A new sprint of the team, already ``active``: saving the sprint starts it (HU-07);
        closing it belongs to HU-10."""
        return cls(
            sprint_id=sprint_id,
            team_id=team_id,
            period=period,
            daily_time=daily_time,
            participants=participants,
            status=SprintStatus.ACTIVE,
        )

    # ------------------------------------------------------------ read state --
    @property
    def team_id(self) -> UUID:
        return self._team_id

    @property
    def period(self) -> SprintPeriod:
        return self._period

    @property
    def daily_time(self) -> DailyTime:
        return self._daily_time

    @property
    def participants(self) -> tuple[UUID, ...]:
        """The daily's participants, in turn order."""
        return self._participants

    @property
    def status(self) -> SprintStatus:
        return self._status

    # -------------------------------------------------------------- behavior --
    def reconfigure(
        self, *, period: SprintPeriod, daily_time: DailyTime, participants: Sequence[UUID]
    ) -> None:
        """Replace the period, the daily's time (with its capture time zone) and the
        participants with their order. The status does not change."""
        self._period = period
        self._daily_time = daily_time
        self._participants = tuple(participants)
