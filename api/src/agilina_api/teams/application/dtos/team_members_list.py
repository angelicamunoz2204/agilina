from dataclasses import dataclass

from agilina_api.teams.application.dtos.member_view import MemberView
from agilina_api.teams.application.dtos.role_option import RoleOption


@dataclass(frozen=True)
class TeamMembersList:
    """The team's active members and the roles that can be given to them (HU-06)."""

    roles: tuple[RoleOption, ...]
    members: tuple[MemberView, ...]
