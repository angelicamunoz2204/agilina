"""Repository interfaces of the identity domain: one per aggregate, in its language.

Implementations live in ``infrastructure``; the domain only states what it needs.
"""

from agilina_api.identity.domain.repositories.invitation_repository import InvitationRepository
from agilina_api.identity.domain.repositories.user_repository import UserRepository

__all__ = [
    "InvitationRepository",
    "UserRepository",
]
