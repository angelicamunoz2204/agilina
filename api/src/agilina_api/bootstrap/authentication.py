"""The adapter that resolves bearer tokens to users, closed until login exists.

The API has no login yet (HU-03): it cannot validate a Keycloak token, so it must not
trust any. Every token is turned away, which makes the routes that need a user answer
``401 not_authenticated``: never a ``500`` and never data. The tests replace the port with
a double that knows its tokens.
"""

from uuid import UUID

from agilina_api.shared.application.access import AuthenticatedUsers


class ClosedAuthenticatedUsers(AuthenticatedUsers):
    """Knows no token, so no request is authenticated.

    TODO(HU-03): replace it with an adapter that validates the Keycloak access token
    (signature against the realm's keys, issuer, audience and expiry) and resolves its
    ``sub`` to the ``app_user`` with ``UserRepository.get_by_keycloak_subject``, keeping
    the contract of ``AuthenticatedUsers``. Only the wiring in ``container.py`` changes.
    """

    async def user_id_for(self, bearer_token: str) -> UUID | None:
        return None
