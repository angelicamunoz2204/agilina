from dataclasses import dataclass

from agilina_api.teams.application.dtos.member_record import MemberRecord
from agilina_shared.enums import OperationMode


@dataclass(frozen=True)
class TeamMemberRecords:
    """A team's active members and whether it has a sprint in progress, read together: what
    the members list needs to tell which changes are blocked and why (HU-06)."""

    members: tuple[MemberRecord, ...]
    has_active_sprint: bool
    mode: OperationMode
    """The team's mode: with each role it gives the label to show (HU-04)."""
