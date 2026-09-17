"""Base declarativa de SQLAlchemy.

La convención de nombres se fija aquí para que Alembic genere migraciones con
nombres estables de índices y restricciones; sin ella, renombrar una
restricción se vuelve una migración manual.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Todas las tablas del dominio heredan de aquí.

    Las entidades llegan con las historias que las necesitan; el modelo de
    datos v0.1 está en el documento de arquitectura.
    """

    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)
