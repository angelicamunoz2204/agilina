"""Cryptographically random activation tokens."""

import secrets

from agilina_api.identity.application.ports.outbound import ActivationTokenGenerator
from agilina_api.identity.domain.value_objects import ActivationToken

TOKEN_BYTES = 32  # 256 bits


class SecretsActivationTokenGenerator(ActivationTokenGenerator):
    def generate(self) -> ActivationToken:
        return ActivationToken(secrets.token_urlsafe(TOKEN_BYTES))
