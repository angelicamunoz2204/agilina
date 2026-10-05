"""Builders of the identity commands (the input of the use cases)."""

from dataclasses import dataclass, field, replace
from typing import Self
from uuid import UUID

from agilina_api.identity.application.commands.activate_account import ActivateAccount
from agilina_api.identity.application.commands.issue_invitation import IssueInvitation
from agilina_api.identity.application.commands.request_new_invitation import RequestNewInvitation
from agilina_shared.enums import Language, TeamRole
from tests.api.builders.defaults import EMAIL, FULL_NAME, PASSWORD, TEAM_NAME, TOKEN
from tests.api.builders.identifiers import next_id


@dataclass(frozen=True)
class IssueInvitationBuilder:
    """The operator invites Julián Torres to Atlas as a member, in Spanish."""

    team_id: UUID = field(default_factory=next_id)
    team_name: str = TEAM_NAME
    email: str = EMAIL
    full_name: str = FULL_NAME
    role: TeamRole = TeamRole.MEMBER
    language: Language = Language.ES
    created_by: UUID | None = None
    inviter_name: str | None = None

    def for_team(self, team_id: UUID, name: str = TEAM_NAME) -> Self:
        return replace(self, team_id=team_id, team_name=name)

    def with_email(self, email: str) -> Self:
        return replace(self, email=email)

    def named(self, full_name: str) -> Self:
        return replace(self, full_name=full_name)

    def as_admin(self) -> Self:
        return replace(self, role=TeamRole.ADMIN)

    def in_language(self, language: Language) -> Self:
        return replace(self, language=language)

    def invited_by(self, user_id: UUID, name: str | None = None) -> Self:
        return replace(self, created_by=user_id, inviter_name=name)

    def signed_by(self, inviter_name: str) -> Self:
        return replace(self, inviter_name=inviter_name)

    def build(self) -> IssueInvitation:
        return IssueInvitation(
            team_id=self.team_id,
            team_name=self.team_name,
            email=self.email,
            full_name=self.full_name,
            role=self.role,
            language=self.language,
            created_by=self.created_by,
            inviter_name=self.inviter_name,
        )


@dataclass(frozen=True)
class ActivateAccountBuilder:
    token: str = TOKEN
    password: str = PASSWORD

    def with_token(self, token: str) -> Self:
        return replace(self, token=token)

    def with_password(self, password: str) -> Self:
        return replace(self, password=password)

    def build(self) -> ActivateAccount:
        return ActivateAccount(token=self.token, password=self.password)


@dataclass(frozen=True)
class RequestNewInvitationBuilder:
    token: str = TOKEN

    def with_token(self, token: str) -> Self:
        return replace(self, token=token)

    def build(self) -> RequestNewInvitation:
        return RequestNewInvitation(token=self.token)
