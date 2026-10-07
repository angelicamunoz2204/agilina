from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateTeamAsAdmin:
    name: str
    user_id: UUID
    """The authenticated user who creates it: never taken from the request body."""
