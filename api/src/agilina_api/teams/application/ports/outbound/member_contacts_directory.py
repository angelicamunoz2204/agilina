"""Port to the identity context: how the members of a team are called and reached."""

from collections.abc import Collection
from typing import Protocol
from uuid import UUID

from agilina_api.teams.application.dtos import MemberContact


class MemberContactsDirectory(Protocol):
    """Teams cannot import identity (AD-21), which owns people's names and emails, so it
    asks for them through this port; the composition root implements it."""

    async def contacts_of(self, user_ids: Collection[UUID]) -> dict[UUID, MemberContact]:
        """The name and email of each of those users, by id, whether or not their account
        is active; a user without an account is left out."""
        ...
