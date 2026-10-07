"""Builders of the teams commands that manage members (HU-06) and configure the sprint
(HU-07): the input of the use cases."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Self
from uuid import UUID

from agilina_api.teams.application.commands.change_member_role import ChangeMemberRole
from agilina_api.teams.application.commands.reconfigure_sprint import ReconfigureSprint
from agilina_api.teams.application.commands.remove_member import RemoveMember
from agilina_api.teams.application.commands.start_sprint import StartSprint
from agilina_shared.enums import TeamRole
from tests.api.builders.defaults import DAILY_TIME, DAILY_TIME_ZONE, SPRINT_END, SPRINT_START
from tests.api.builders.identifiers import next_id


@dataclass(frozen=True)
class ChangeMemberRoleBuilder:
    """An admin makes a member of the team an admin."""

    team_id: UUID = field(default_factory=next_id)
    user_id: UUID = field(default_factory=next_id)
    role: TeamRole = TeamRole.ADMIN
    requested_by: UUID = field(default_factory=next_id)

    def for_team(self, team_id: UUID) -> Self:
        return replace(self, team_id=team_id)

    def of_user(self, user_id: UUID) -> Self:
        return replace(self, user_id=user_id)

    def to_role(self, role: TeamRole) -> Self:
        return replace(self, role=role)

    def requested_by_admin(self, user_id: UUID) -> Self:
        return replace(self, requested_by=user_id)

    def build(self) -> ChangeMemberRole:
        return ChangeMemberRole(
            team_id=self.team_id,
            user_id=self.user_id,
            role=self.role,
            requested_by=self.requested_by,
        )


@dataclass(frozen=True)
class RemoveMemberBuilder:
    """An admin takes a member out of the team."""

    team_id: UUID = field(default_factory=next_id)
    user_id: UUID = field(default_factory=next_id)
    requested_by: UUID = field(default_factory=next_id)

    def for_team(self, team_id: UUID) -> Self:
        return replace(self, team_id=team_id)

    def of_user(self, user_id: UUID) -> Self:
        return replace(self, user_id=user_id)

    def requested_by_admin(self, user_id: UUID) -> Self:
        return replace(self, requested_by=user_id)

    def build(self) -> RemoveMember:
        return RemoveMember(
            team_id=self.team_id, user_id=self.user_id, requested_by=self.requested_by
        )


@dataclass(frozen=True)
class _SprintConfigurationBuilder:
    """What an admin sends to start or edit the sprint: the defaults of ``SprintBuilder``
    (2026-10-05 to 2026-10-16, the daily at 09:00 in America/Bogota) and no participants."""

    team_id: UUID = field(default_factory=next_id)
    start_date: date = SPRINT_START
    end_date: date = SPRINT_END
    daily_time: datetime = DAILY_TIME
    time_zone: str = DAILY_TIME_ZONE
    participants: tuple[UUID, ...] = ()

    def for_team(self, team_id: UUID) -> Self:
        return replace(self, team_id=team_id)

    def with_period(self, start: date, end: date) -> Self:
        return replace(self, start_date=start, end_date=end)

    def with_daily_time(self, at: datetime, time_zone: str) -> Self:
        return replace(self, daily_time=at, time_zone=time_zone)

    def with_participants(self, *user_ids: UUID) -> Self:
        """The daily's participants, in turn order."""
        return replace(self, participants=user_ids)


@dataclass(frozen=True)
class StartSprintBuilder(_SprintConfigurationBuilder):
    """An admin configures the team's sprint, which starts active."""

    def build(self) -> StartSprint:
        return StartSprint(
            team_id=self.team_id,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_time=self.daily_time,
            time_zone=self.time_zone,
            participants=self.participants,
        )


@dataclass(frozen=True)
class ReconfigureSprintBuilder(_SprintConfigurationBuilder):
    """An admin edits the team's active sprint."""

    def build(self) -> ReconfigureSprint:
        return ReconfigureSprint(
            team_id=self.team_id,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_time=self.daily_time,
            time_zone=self.time_zone,
            participants=self.participants,
        )
