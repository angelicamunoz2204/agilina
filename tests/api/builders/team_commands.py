"""Builders of the teams commands that manage members (the input of the use cases)."""

from dataclasses import dataclass, field, replace
from typing import Self
from uuid import UUID

from agilina_api.teams.application.commands.change_member_role import ChangeMemberRole
from agilina_api.teams.application.commands.remove_member import RemoveMember
from agilina_shared.enums import TeamRole
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
