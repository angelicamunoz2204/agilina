"""Column helpers shared by every context's ORM models."""

from enum import Enum

from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.exc import IntegrityError


def pg_enum[E: Enum](enum_class: type[E], name: str) -> ENUM:
    """A column typed with an enum that already exists in PostgreSQL (the migrations
    create it). It stores the enum's *values* (``'pending'``), not its member names."""
    return ENUM(
        enum_class,
        name=name,
        create_type=False,
        values_callable=lambda members: [member.value for member in members],
    )


def violated_constraint(error: IntegrityError) -> str | None:
    """Name of the constraint or unique index that an ``IntegrityError`` violated."""
    diagnostics = getattr(error.orig, "diag", None)
    return getattr(diagnostics, "constraint_name", None)
