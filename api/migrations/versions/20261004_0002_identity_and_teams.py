"""identity and teams: the tables HU-02 needs

Creates ``app_user``, ``team``, ``team_member`` and ``invitation`` exactly as the
reference schema (``agilina_schema.sql``) defines them, with the one change of AD-22:
``team.created_by`` and ``invitation.created_by`` accept NULL, meaning "created by the
platform operator" (the first admin of a team has nobody to be created by).

Written as SQL on purpose, like every migration of this project: enums, triggers and
partial indexes are not something autogenerate reproduces, and the foreign keys between
contexts live here and not in the ORM models (each context's models know only their own
tables).

Revision ID: 0002_identity_and_teams
Previous revision: 0001_base
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_identity_and_teams"
down_revision: str | None = "0001_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE = [
    # Case-insensitive text for emails.
    "CREATE EXTENSION IF NOT EXISTS citext",
    # ------------------------------------------------------------------ enums --
    "CREATE TYPE team_mode AS ENUM ('support', 'autonomous')",
    "CREATE TYPE team_language AS ENUM ('en', 'es')",
    "CREATE TYPE team_role AS ENUM ('admin', 'member')",
    "CREATE TYPE membership_status AS ENUM ('active', 'removed')",
    "CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'expired', 'revoked')",
    # --------------------------------------------------- updated_at maintenance --
    """
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
    BEGIN
        NEW.updated_at := now();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """,
    # --------------------------------------------------------------- app_user --
    """
    CREATE TABLE app_user (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        keycloak_subject  TEXT        NOT NULL UNIQUE,
        email             CITEXT      NOT NULL UNIQUE,
        full_name         TEXT        NOT NULL,
        is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "COMMENT ON TABLE app_user IS 'Agilina user. Passwords and sessions live in Keycloak (AD-12).'",
    "COMMENT ON COLUMN app_user.keycloak_subject IS "
    "'The \"sub\" claim of the OIDC token: the only link with the identity provider.'",
    "CREATE TRIGGER trg_app_user_updated BEFORE UPDATE ON app_user "
    "FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    # ------------------------------------------------------------------- team --
    """
    CREATE TABLE team (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name        TEXT          NOT NULL,
        mode        team_mode     NOT NULL DEFAULT 'support',
        language    team_language NOT NULL DEFAULT 'en',
        created_by  UUID          REFERENCES app_user(id) ON DELETE RESTRICT,
        silence_threshold_seconds     SMALLINT NOT NULL DEFAULT 10
            CHECK (silence_threshold_seconds  BETWEEN 3 AND 120),
        stuck_turn_threshold_seconds  SMALLINT NOT NULL DEFAULT 30
            CHECK (stuck_turn_threshold_seconds BETWEEN 5 AND 300),
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT team_name_not_blank CHECK (length(btrim(name)) > 0)
    )
    """,
    "COMMENT ON COLUMN team.mode IS "
    "'Only effect: whether Agilina asks for approval before acting (HU-11, HU-42, HU-43).'",
    "COMMENT ON COLUMN team.created_by IS "
    "'NULL when the platform operator created the team to give it its first admin (AD-22).'",
    "COMMENT ON TABLE team IS "
    "'No time zone: members can live in different countries (AD-20).'",
    "CREATE TRIGGER trg_team_updated BEFORE UPDATE ON team "
    "FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    # ------------------------------------------------------------ team_member --
    # The visible label (Admin / Scrum Master / Member) is NOT stored: it is derived
    # from role + team.mode (HU-04).
    """
    CREATE TABLE team_member (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        team_id        UUID              NOT NULL REFERENCES team(id)     ON DELETE CASCADE,
        user_id        UUID              NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
        role           team_role         NOT NULL DEFAULT 'member',
        status         membership_status NOT NULL DEFAULT 'active',
        slack_user_id  TEXT,
        joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        removed_at     TIMESTAMPTZ,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT team_member_unique UNIQUE (team_id, user_id),
        CONSTRAINT team_member_removed_coherent
            CHECK ((status = 'removed') = (removed_at IS NOT NULL))
    )
    """,
    "CREATE UNIQUE INDEX team_member_slack_unique "
    "ON team_member (team_id, slack_user_id) WHERE slack_user_id IS NOT NULL",
    "CREATE INDEX team_member_user_idx ON team_member (user_id) WHERE status = 'active'",
    "CREATE TRIGGER trg_team_member_updated BEFORE UPDATE ON team_member "
    "FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
    # ------------------------------------------------------------- invitation --
    # HU-02: no public registration. Single-use link that expires after 7 days.
    """
    CREATE TABLE invitation (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        team_id           UUID              NOT NULL REFERENCES team(id) ON DELETE CASCADE,
        email             CITEXT            NOT NULL,
        full_name         TEXT              NOT NULL,
        role              team_role         NOT NULL DEFAULT 'member',
        token_hash        TEXT              NOT NULL UNIQUE,
        status            invitation_status NOT NULL DEFAULT 'pending',
        expires_at        TIMESTAMPTZ       NOT NULL,
        created_by        UUID              REFERENCES team_member(id) ON DELETE RESTRICT,
        accepted_at       TIMESTAMPTZ,
        accepted_user_id  UUID REFERENCES app_user(id) ON DELETE SET NULL,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "COMMENT ON COLUMN invitation.token_hash IS "
    "'Only the hash. The clear token travels once, by email, and is never stored.'",
    "COMMENT ON COLUMN invitation.created_by IS "
    "'NULL when the platform operator issued it, to create a team''s first admin (AD-22).'",
    "CREATE UNIQUE INDEX invitation_pending_unique "
    "ON invitation (team_id, email) WHERE status = 'pending'",
]

DOWNGRADE = [
    "DROP TABLE invitation",
    "DROP TABLE team_member",
    "DROP TABLE team",
    "DROP TABLE app_user",
    "DROP FUNCTION set_updated_at()",
    "DROP TYPE invitation_status",
    "DROP TYPE membership_status",
    "DROP TYPE team_role",
    "DROP TYPE team_language",
    "DROP TYPE team_mode",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
