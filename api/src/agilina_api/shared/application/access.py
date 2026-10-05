"""Who is calling and what they may reach: the user of Agilina behind the bearer token of
a request, and their membership in the team the request is about.

Every context needs both and none of them owns them, so the ports live here. Validating the
token is the login story's job (HU-03); until then the composition root wires an adapter
that turns every token away (``bootstrap.authentication``).
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agilina_shared.enums import TeamRole


class NotAuthenticatedError(Exception):
    """The request carries no bearer token, or one that does not identify a user of
    Agilina. Not a business rule: the interface answers it with a ``401``."""


class AuthenticatedUsers(Protocol):
    """Resolves the bearer token of a request to the ``app_user`` it belongs to.

    The contract an adapter must keep (HU-03 only replaces the adapter, not this port):

    - it receives the raw token, without the ``Bearer`` prefix;
    - it validates it completely (signature, issuer, audience and expiry) before trusting
      any of its claims;
    - it returns the ``app_user.id`` of the token's subject (the Keycloak ``sub``), or
      ``None`` when the token is not valid or its subject has no user in Agilina. A bad
      token is an answer, not a failure: it never raises for one;
    - it says nothing about teams or roles. What the user may do in a team is decided
      against the stored membership, never against a claim of the token.
    """

    async def user_id_for(self, bearer_token: str) -> UUID | None: ...


class NotATeamMemberError(Exception):
    """The user is not an active member of the team the request is about. The team may
    not even exist: both answer the same so that nobody can find out which teams exist.
    Not a business rule: the interface answers it with a ``403``."""


@dataclass(frozen=True)
class TeamContext:
    """The team a request is about and the stored role in it of the user who sent it."""

    team_id: UUID
    user_id: UUID
    role: TeamRole


class TeamAccess(Protocol):
    """Tells whether a user belongs to a team, against the stored membership.

    Every route about one team checks it before anything else (HU-05): the team is the
    tenant, so the ``team_id`` is part of the signature and cannot be forgotten.
    """

    async def role_of(self, *, team_id: UUID, user_id: UUID) -> TeamRole | None:
        """The user's role in the team while their membership is active; ``None`` when
        they were never a member, were removed, or the team does not exist."""
        ...
