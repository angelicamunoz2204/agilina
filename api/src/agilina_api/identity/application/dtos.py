"""Data transfer objects of the identity use cases: plain types, no framework."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.domain.value_objects import Email
from agilina_shared.enums import Language, TeamRole


@dataclass(frozen=True)
class InvitationStatusView:
    """What the activation page shows about a link (HU-02)."""

    email: str
    full_name: str
    role: TeamRole
    status: InvitationStatus
    expires_at: datetime


@dataclass(frozen=True)
class IssuedInvitation:
    """The result of issuing an invitation. It never carries the token: that travels only
    in the email."""

    invitation_id: UUID
    expires_at: datetime
    revoked_previous: bool = False
    """Whether the person had a pending invitation whose link still worked, now revoked."""


@dataclass(frozen=True)
class ActivatedAccount:
    """The result of activating an account: who, where and with which role."""

    user_id: UUID
    team_id: UUID
    email: Email
    role: TeamRole


@dataclass(frozen=True)
class Contact:
    """Someone who can be e-mailed."""

    email: Email
    full_name: str


@dataclass(frozen=True)
class TeamContacts:
    """Who to tell about a team: its name, its language and its active admins."""

    team_name: str
    language: Language
    admins: tuple[Contact, ...]


class TeamInvitationOutcome(StrEnum):
    """What inviting a person to a team did (HU-06)."""

    INVITATION_SENT = "invitation_sent"
    """They had no account: they got an invitation with its activation link."""
    MEMBER_ADDED = "member_added"
    """They already had an account: they joined the team and got a notice, without a link."""
