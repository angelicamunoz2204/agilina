"""Who is calling and whether they belong to the team, as FastAPI dependencies every
context can use.

A route that needs to know who is calling declares ``Depends(current_user_id)``: it gets
the ``app_user.id`` or the request ends in ``401 not_authenticated``.

A route about one team has ``{team_id}`` in its path and declares
``Depends(current_team_member)``: it gets the ``TeamContext`` with the caller's stored role,
or the request ends in ``403 not_a_team_member``. That is how every route of a team keeps
the other teams out (HU-05).

The adapters are declared here and provided by the composition root, so this layer never
imports the infrastructure one.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agilina_api.shared.application.access import (
    AuthenticatedUsers,
    NotATeamMemberError,
    NotAuthenticatedError,
    TeamAccess,
    TeamContext,
)

bearer = HTTPBearer(
    auto_error=False,
    description="The access token Keycloak issues at login, in `Authorization: Bearer <token>`.",
)
"""``auto_error=False`` so that a missing token goes through the API's single error handler
and answers with the common ``ErrorResponse``. It also documents the security scheme in
OpenAPI."""


def get_authenticated_users() -> AuthenticatedUsers:
    raise NotImplementedError("Wired by the composition root")


def get_team_access() -> TeamAccess:
    raise NotImplementedError("Wired by the composition root")


async def current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    users: AuthenticatedUsers = Depends(get_authenticated_users),
) -> UUID:
    """The ``app_user.id`` of whoever sent the request."""
    if credentials is None:
        raise NotAuthenticatedError("The request carries no bearer token")
    user_id = await users.user_id_for(credentials.credentials)
    if user_id is None:
        raise NotAuthenticatedError("The bearer token does not identify a user of Agilina")
    return user_id


async def current_team_member(
    team_id: Annotated[UUID, Path(description="The team the request is about.")],
    user_id: UUID = Depends(current_user_id),
    access: TeamAccess = Depends(get_team_access),
) -> TeamContext:
    """The team of the route's ``{team_id}`` and the caller's role in it.

    Generic on purpose: it knows nothing of the route, so any route of a team can use it,
    and a rule on the role (only an admin may…) is another dependency built on top of
    this one. The caller is resolved first, so a request without a valid token answers
    ``401`` before the membership is looked at.
    """
    role = await access.role_of(team_id=team_id, user_id=user_id)
    if role is None:
        raise NotATeamMemberError("The user is not an active member of the team")
    return TeamContext(team_id=team_id, user_id=user_id, role=role)
