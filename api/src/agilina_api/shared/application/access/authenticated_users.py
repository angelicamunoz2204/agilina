from typing import Protocol
from uuid import UUID


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
