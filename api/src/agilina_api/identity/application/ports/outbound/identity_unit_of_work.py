"""One transaction around an identity command, with the repositories it uses."""

from typing import Protocol

from agilina_api.identity.application.ports.outbound.team_membership import TeamMembership
from agilina_api.identity.domain.repositories import InvitationRepository, UserRepository
from agilina_api.shared.application.ports import UnitOfWork


class IdentityUnitOfWork(UnitOfWork, Protocol):
    invitations: InvitationRepository
    users: UserRepository
    team_membership: TeamMembership
