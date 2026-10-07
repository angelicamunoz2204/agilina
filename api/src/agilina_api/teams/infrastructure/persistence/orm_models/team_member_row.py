from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.database.types import pg_enum
from agilina_api.teams.domain.team import MembershipStatus
from agilina_shared.enums import TeamRole


class TeamMemberRow(Base):
    __tablename__ = "team_member"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid)
    user_id: Mapped[UUID] = mapped_column(Uuid)
    role: Mapped[TeamRole] = mapped_column(pg_enum(TeamRole, "team_role"))
    status: Mapped[MembershipStatus] = mapped_column(pg_enum(MembershipStatus, "membership_status"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
