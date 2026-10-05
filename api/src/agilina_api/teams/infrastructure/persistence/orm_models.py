"""ORM rows of the teams context. They mirror the tables; they are *not* the entities.

``team_member.slack_user_id`` is not mapped yet (HU-39): the repository only writes the
columns it knows, so what it does not know stays as it is.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.database.types import pg_enum
from agilina_api.teams.domain.team import MembershipStatus
from agilina_shared.enums import Language, OperationMode, TeamRole


class TeamRow(Base):
    __tablename__ = "team"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    mode: Mapped[OperationMode] = mapped_column(pg_enum(OperationMode, "team_mode"))
    language: Mapped[Language] = mapped_column(pg_enum(Language, "team_language"))
    created_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TeamMemberRow(Base):
    __tablename__ = "team_member"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid)
    user_id: Mapped[UUID] = mapped_column(Uuid)
    role: Mapped[TeamRole] = mapped_column(pg_enum(TeamRole, "team_role"))
    status: Mapped[MembershipStatus] = mapped_column(pg_enum(MembershipStatus, "membership_status"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
