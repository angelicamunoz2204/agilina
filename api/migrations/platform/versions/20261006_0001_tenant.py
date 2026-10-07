"""tenant: the catalog of the organizations the platform serves (AD-29)

One row per tenant. The tenant's database and realm are not stored: they are derived from the
slug (``agilina_<slug>`` and ``agilina-<slug>``), so the catalog cannot disagree with them.

Written as SQL on purpose, like every migration of this project.

Revision ID: 0001_tenant
Previous revision: none
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_tenant"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE tenant_status AS ENUM ('active', 'suspended')")
    op.execute(
        """
        CREATE TABLE tenant (
            slug          TEXT PRIMARY KEY,
            display_name  TEXT          NOT NULL,
            language      TEXT          NOT NULL DEFAULT 'es',
            status        tenant_status NOT NULL DEFAULT 'active',
            created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
            CONSTRAINT tenant_slug_format CHECK (slug ~ '^[a-z][a-z0-9]{1,30}$'),
            CONSTRAINT tenant_slug_reserved CHECK (slug NOT IN ('platform', 'admin', 'api')),
            CONSTRAINT tenant_display_name_not_blank CHECK (btrim(display_name) <> ''),
            CONSTRAINT tenant_language_known CHECK (language IN ('es', 'en'))
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE tenant")
    op.execute("DROP TYPE tenant_status")
