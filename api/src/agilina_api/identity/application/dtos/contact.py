from dataclasses import dataclass

from agilina_api.identity.domain.value_objects import Email


@dataclass(frozen=True)
class Contact:
    """Someone who can be e-mailed."""

    email: Email
    full_name: str
