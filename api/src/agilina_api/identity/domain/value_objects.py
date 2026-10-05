"""Value objects of the identity domain: immutable and valid by construction."""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Self

from agilina_api.identity.domain.errors import (
    InvalidActivationTokenError,
    InvalidEmailError,
    InvalidTokenHashError,
)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_EMAIL_LENGTH = 254  # RFC 5321
_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")  # 32 random bytes, url-safe base64 without padding
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


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


@dataclass(frozen=True)
class TokenHash:
    """SHA-256 of an activation token. It is the only form in which a token is stored."""

    value: str

    def __post_init__(self) -> None:
        if not _SHA256_HEX.match(self.value):
            raise InvalidTokenHashError("A token hash is 64 lowercase hexadecimal characters")


@dataclass(frozen=True)
class ActivationToken:
    """The secret of an invitation link.

    It exists in clear only for a moment: it is generated, e-mailed and forgotten.
    What is stored is ``hash()``. It never shows in a ``repr`` or a log.
    """

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not _TOKEN.match(self.value):
            raise InvalidActivationTokenError("Not an activation token")

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Read a token out of a link; an altered one raises ``InvalidActivationTokenError``."""
        return cls(raw.strip())

    def hash(self) -> TokenHash:
        return TokenHash(hashlib.sha256(self.value.encode("ascii")).hexdigest())
