"""The ``Invitation`` aggregate: permission, for one person, to enter one team.

There is no public registration (HU-02): an admin issues an invitation and the person
activates their account from a single-use link that expires after seven days. Only the
SHA-256 of the link's token is stored.
"""

from agilina_api.identity.domain.invitation.invitation import VALIDITY, Invitation
from agilina_api.identity.domain.invitation.invitation_status import InvitationStatus

__all__ = [
    "Invitation",
    "InvitationStatus",
    "VALIDITY",
]
