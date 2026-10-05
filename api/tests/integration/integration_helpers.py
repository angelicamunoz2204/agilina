"""Helpers shared by the integration tests: database set-up and entity builders."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from alembic.config import Config
from sqlalchemy import create_engine, text

from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import ActivationToken, Email
from agilina_api.teams.domain.team import Team
from agilina_shared.enums import TeamRole

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
API_DIR = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "migrations"))
    return config


def create_database(admin_dsn: str, name: str) -> None:
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine.dispose()


def drop_database(admin_dsn: str, name: str) -> None:
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    engine.dispose()


def make_team(**overrides: object) -> Team:
    fields: dict[str, object] = {
        "team_id": uuid4(),
        "name": "Atlas",
        "created_by": None,
        "now": NOW,
    }
    fields.update(overrides)
    return Team.create(**fields)  # type: ignore[arg-type]


def make_user(**overrides: object) -> AppUser:
    fields: dict[str, object] = {
        "user_id": uuid4(),
        "keycloak_subject": f"subject-{uuid4()}",
        "email": Email(f"{uuid4().hex[:8]}@example.test"),
        "full_name": "Julián Torres",
        "now": NOW,
    }
    fields.update(overrides)
    return AppUser.register(**fields)  # type: ignore[arg-type]


def make_token() -> ActivationToken:
    import secrets

    return ActivationToken(secrets.token_urlsafe(32))


def make_invitation(
    team_id: UUID,
    email: str = "julian@example.test",
    token: ActivationToken | None = None,
    **o: object,
) -> tuple[Invitation, ActivationToken]:
    token = token or make_token()
    fields: dict[str, object] = {
        "invitation_id": uuid4(),
        "team_id": team_id,
        "email": Email(email),
        "full_name": "Julián Torres",
        "role": TeamRole.MEMBER,
        "token_hash": token.hash(),
        "created_by": None,
        "now": NOW,
    }
    fields.update(o)
    return Invitation.issue(**fields), token  # type: ignore[arg-type]
