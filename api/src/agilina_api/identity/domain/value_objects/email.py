import re
from dataclasses import dataclass

from agilina_api.identity.domain.errors import InvalidEmailError

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


_MAX_EMAIL_LENGTH = 254  # RFC 5321


@dataclass(frozen=True)
class Email:
    """An email address, trimmed and lowercased.

    The database compares emails case-insensitively (CITEXT); normalizing here makes
    the domain agree with it.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if len(normalized) > _MAX_EMAIL_LENGTH or not _EMAIL.match(normalized):
            raise InvalidEmailError("Not a valid email address")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
