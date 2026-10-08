"""Errors of the teams domain."""

from agilina_api.teams.domain.errors.active_sprint_exists_error import ActiveSprintExistsError
from agilina_api.teams.domain.errors.already_member_error import AlreadyMemberError
from agilina_api.teams.domain.errors.daily_participant_not_a_member_error import (
    DailyParticipantNotAMemberError,
)
from agilina_api.teams.domain.errors.duplicate_daily_participant_error import (
    DuplicateDailyParticipantError,
)
from agilina_api.teams.domain.errors.invalid_team_name_error import InvalidTeamNameError
from agilina_api.teams.domain.errors.invalid_time_zone_error import InvalidTimeZoneError
from agilina_api.teams.domain.errors.last_admin_error import LastAdminError
from agilina_api.teams.domain.errors.member_not_found_error import MemberNotFoundError
from agilina_api.teams.domain.errors.no_active_sprint_error import NoActiveSprintError
from agilina_api.teams.domain.errors.no_daily_participants_error import NoDailyParticipantsError
from agilina_api.teams.domain.errors.role_change_during_active_sprint_error import (
    RoleChangeDuringActiveSprintError,
)
from agilina_api.teams.domain.errors.sprint_ends_before_start_error import (
    SprintEndsBeforeStartError,
)
from agilina_api.teams.domain.errors.team_not_found_error import TeamNotFoundError

__all__ = [
    "ActiveSprintExistsError",
    "AlreadyMemberError",
    "DailyParticipantNotAMemberError",
    "DuplicateDailyParticipantError",
    "InvalidTeamNameError",
    "InvalidTimeZoneError",
    "LastAdminError",
    "MemberNotFoundError",
    "NoActiveSprintError",
    "NoDailyParticipantsError",
    "RoleChangeDuringActiveSprintError",
    "SprintEndsBeforeStartError",
    "TeamNotFoundError",
]
