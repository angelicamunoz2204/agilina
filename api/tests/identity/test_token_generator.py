"""Activation tokens are 256 bits of cryptographic randomness."""

from agilina_api.identity.domain.value_objects import ActivationToken
from agilina_api.identity.infrastructure.tokens import SecretsActivationTokenGenerator


def test_a_generated_token_is_a_valid_activation_token_of_256_bits():
    token = SecretsActivationTokenGenerator().generate()

    assert ActivationToken.parse(token.value) == token  # the shape the link will carry
    assert len(token.value) == 43  # 32 bytes in url-safe base64 without padding


def test_generated_tokens_do_not_repeat_and_hash_differently():
    generator = SecretsActivationTokenGenerator()

    tokens = [generator.generate() for _ in range(200)]

    assert len({token.value for token in tokens}) == 200
    assert len({token.hash().value for token in tokens}) == 200
