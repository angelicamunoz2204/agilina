from dataclasses import dataclass

from agilina_api.teams.application.dtos.member_record import MemberRecord


@dataclass(frozen=True)
class TeamMemberRecords:
    """A team's active members and whether it has a sprint in progress, read together: what
    the members list needs to tell which changes are blocked and why (HU-06)."""

    members: tuple[MemberRecord, ...]
    has_active_sprint: bool
