"""Port for producing the secret of an invitation link."""

from typing import Protocol

from agilina_api.identity.domain.value_objects import ActivationToken


class ActivationTokenGenerator(Protocol):
    """A port so tests can use a known token; the real one is cryptographically random."""

    def generate(self) -> ActivationToken: ...
