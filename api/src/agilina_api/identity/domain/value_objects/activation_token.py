import hashlib
import re
from dataclasses import dataclass, field
from typing import Self

from agilina_api.identity.domain.errors import InvalidActivationTokenError
from agilina_api.identity.domain.value_objects.token_hash import TokenHash

_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")  # 32 random bytes, url-safe base64 without padding


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
