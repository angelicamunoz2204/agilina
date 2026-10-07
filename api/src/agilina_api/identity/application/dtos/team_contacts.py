from dataclasses import dataclass

from agilina_api.identity.application.dtos.contact import Contact
from agilina_shared.enums import Language


@dataclass(frozen=True)
class TeamContacts:
    """Who to tell about a team: its name, its language and its active admins."""

    team_name: str
    language: Language
    admins: tuple[Contact, ...]
