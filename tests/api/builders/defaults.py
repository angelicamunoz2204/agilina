"""The values every builder starts from."""

from datetime import UTC, datetime

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
"""The instant the fake clock starts at and the default moment things are created."""

TOKEN = "T" * 43
"""A well-formed activation token (43 characters, like ``token_urlsafe(32)``)."""

PASSWORD = "a-long-enough-password"  # noqa: S105 - a test value

EMAIL = "julian@example.test"
FULL_NAME = "Julián Torres"
TEAM_NAME = "Atlas"
