"""What to do with the invitation a person already has when they are invited again."""

from datetime import datetime
from uuid import UUID

from agilina_api.identity.application.ports.outbound import IdentityUnitOfWork
from agilina_api.identity.domain.value_objects import Email


async def release_pending_invitation(
    uow: IdentityUnitOfWork, team_id: UUID, email: Email, now: datetime
) -> bool:
    """Close the invitation stored as pending for that email in that team, if any, so a new
    one can take its place (HU-06: the new invitation invalidates the previous one).

    One past its deadline is marked expired; one whose link still works is revoked, so that
    link stops working. Either way it is saved before the caller stores anything new: the
    index allows a single pending invitation per email and team. Returns whether a link
    that still worked was revoked.
    """
    existing = await uow.invitations.find_pending(team_id, email)
    if existing is None:
        return False
    revoked = not existing.expire_if_due(now)
    if revoked:
        existing.revoke(now)
    await uow.invitations.save(existing)
    return revoked
