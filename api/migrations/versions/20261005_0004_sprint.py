"""sprint: the minimal sprint table, to know whether a team has a sprint in progress (HU-06)

Only what answers "does the team have an active sprint?": the team, the dates and the
status. HU-07 extends it with the daily's time, its participants and their order.

The statuses are the glossary's (``planned``, ``active``, ``closed``), so HU-07 needs no
``ALTER TYPE``. A team has at most one active sprint, which the partial unique index makes
the database enforce.

Revision ID: 0004_sprint
Previous revision: 0003_team_name_max_length
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_sprint"
down_revision: str | None = "0003_team_name_max_length"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE = [
    "CREATE TYPE sprint_status AS ENUM ('planned', 'active', 'closed')",
    """
    CREATE TABLE sprint (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        team_id     UUID          NOT NULL REFERENCES team(id) ON DELETE CASCADE,
        start_date  DATE          NOT NULL,
        end_date    DATE          NOT NULL,
        status      sprint_status NOT NULL DEFAULT 'planned',
        created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
        updated_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
        CONSTRAINT sprint_dates_ordered CHECK (end_date >= start_date)
    )
    """,
    "COMMENT ON TABLE sprint IS "
    "'Minimal sprint (HU-06): enough to know whether a team has one in progress. "
    "HU-07 extends it with the daily''s time, participants and order.'",
    "CREATE INDEX sprint_team_idx ON sprint (team_id)",
    "CREATE UNIQUE INDEX sprint_one_active_per_team ON sprint (team_id) WHERE status = 'active'",
    "CREATE TRIGGER trg_sprint_updated BEFORE UPDATE ON sprint "
    "FOR EACH ROW EXECUTE FUNCTION set_updated_at()",
]

DOWNGRADE = [
    "DROP TABLE sprint",
    "DROP TYPE sprint_status",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
