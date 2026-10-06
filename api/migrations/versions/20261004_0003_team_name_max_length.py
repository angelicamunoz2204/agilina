"""team name max length: a team's name has at most 80 characters (HU-05)

Backs the ``TeamName`` rule of the domain in the database. The check is on the stored
name, which the domain has already trimmed, and ``char_length`` counts characters like
Python's ``len`` does, so both sides agree on where the limit is.

Revision ID: 0003_team_name_max_length
Previous revision: 0002_identity_and_teams
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_team_name_max_length"
down_revision: str | None = "0002_identity_and_teams"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE = [
    "ALTER TABLE team ADD CONSTRAINT team_name_max_length CHECK (char_length(name) <= 80)",
]

DOWNGRADE = [
    "ALTER TABLE team DROP CONSTRAINT team_name_max_length",
]


def upgrade() -> None:
    for statement in UPGRADE:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE:
        op.execute(statement)
