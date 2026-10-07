import re
from dataclasses import dataclass

from agilina_api.identity.domain.errors import InvalidTokenHashError

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class TokenHash:
    """SHA-256 of an activation token. It is the only form in which a token is stored."""

    value: str

    def __post_init__(self) -> None:
        if not _SHA256_HEX.match(self.value):
            raise InvalidTokenHashError("A token hash is 64 lowercase hexadecimal characters")
