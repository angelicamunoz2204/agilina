"""SQLAlchemy declarative base.

The naming convention is fixed here so Alembic generates migrations with stable
index and constraint names; without it, renaming a constraint becomes a manual
migration.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Every ORM model of every context inherits from here.

    Entities arrive with the stories that need them; the data model v0.1 is in
    the architecture document.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
