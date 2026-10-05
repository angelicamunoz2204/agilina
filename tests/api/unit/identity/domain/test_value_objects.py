"""Value objects are valid by construction: an invalid one cannot exist."""

import hashlib
import secrets

import pytest

from agilina_api.identity.domain.errors import (
    InvalidActivationTokenError,
    InvalidEmailError,
    InvalidTokenHashError,
)
from agilina_api.identity.domain.value_objects import ActivationToken, Email, TokenHash


def _token_text() -> str:
    return secrets.token_urlsafe(32)


@pytest.mark.parametrize(
    "raw", ["julian@example.test", "  Julian@Example.TEST  ", "a.b+c@sub.example.org"]
)
def test_a_valid_email_is_trimmed_and_lowercased(raw: str):
    assert Email(raw).value == raw.strip().lower()


@pytest.mark.parametrize(
    "raw", ["", "no-at-sign", "two@@example.test", "spaces in@example.test", "a@nodot", "a@b."]
)
def test_an_invalid_email_cannot_be_built(raw: str):
    with pytest.raises(InvalidEmailError):
        Email(raw)


def test_an_email_longer_than_the_standard_allows_is_rejected():
    with pytest.raises(InvalidEmailError):
        Email("a" * 250 + "@example.test")


def test_two_emails_that_differ_only_in_case_are_equal():
    assert Email("Julian@Example.test") == Email("julian@example.test")


def test_a_token_hash_is_a_sha256_in_lowercase_hexadecimal():
    TokenHash(hashlib.sha256(b"x").hexdigest())
    for bad in ("", "abc", "G" * 64, hashlib.sha256(b"x").hexdigest().upper()):
        with pytest.raises(InvalidTokenHashError):
            TokenHash(bad)


def test_a_generated_token_is_accepted_and_hashes_to_its_sha256():
    text = _token_text()

    token = ActivationToken.parse(text)

    assert token.hash().value == hashlib.sha256(text.encode()).hexdigest()


def test_the_hash_of_a_token_is_stable_and_different_tokens_hash_differently():
    first, second = _token_text(), _token_text()

    assert ActivationToken(first).hash() == ActivationToken(first).hash()
    assert ActivationToken(first).hash() != ActivationToken(second).hash()


@pytest.mark.parametrize(
    "altered", ["", "short", "x" * 42, "x" * 44, "has spaces " + "x" * 32, "+/=" * 15]
)
def test_an_altered_link_is_not_a_token(altered: str):
    with pytest.raises(InvalidActivationTokenError):
        ActivationToken.parse(altered)


def test_the_token_never_shows_in_its_representation():
    text = _token_text()

    token = ActivationToken(text)

    assert text not in repr(token)
    assert text not in str(token) or str(token) == repr(token)  # dataclass str is repr
