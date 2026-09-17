"""base: punto de partida del historial de migraciones

Revisión vacía a propósito. Existe para que toda migración posterior tenga un
padre estable y para que `alembic upgrade head` funcione desde un clon limpio
antes de que exista la primera entidad del dominio.

ID de revisión: 0001_base
Revisión anterior: ninguna
"""

from collections.abc import Sequence

revision: str = "0001_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
