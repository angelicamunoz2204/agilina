"""Data Builders: they put together the objects the tests need.

Every builder starts from valid, fixed defaults, changes one thing per ``with_…`` call
(each call returns a new builder, so a shared baseline is never altered) and builds the
object through the domain's own rules. A state like "used" or "expired" is reached by
behavior (``Invitation.accept``), never by writing private fields.
"""

from tests.api.builders.contacts import ContactBuilder, TeamContactsBuilder
from tests.api.builders.defaults import NOW, PASSWORD, TOKEN
from tests.api.builders.email_message import EmailMessageBuilder
from tests.api.builders.identifiers import next_id, reset_ids
from tests.api.builders.identity_commands import (
    ActivateAccountBuilder,
    IssueInvitationBuilder,
    RequestNewInvitationBuilder,
)
from tests.api.builders.invitation import InvitationBuilder
from tests.api.builders.team import TeamBuilder
from tests.api.builders.user import AppUserBuilder

__all__ = [
    "NOW",
    "PASSWORD",
    "TOKEN",
    "ActivateAccountBuilder",
    "AppUserBuilder",
    "ContactBuilder",
    "EmailMessageBuilder",
    "InvitationBuilder",
    "IssueInvitationBuilder",
    "RequestNewInvitationBuilder",
    "TeamBuilder",
    "TeamContactsBuilder",
    "next_id",
    "reset_ids",
]
