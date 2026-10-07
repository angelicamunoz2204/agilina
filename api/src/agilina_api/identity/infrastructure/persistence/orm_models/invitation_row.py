from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Text, Uuid
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.database.types import pg_enum
from agilina_shared.enums import TeamRole


class InvitationRow(Base):
    __tablename__ = "invitation"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid)
    email: Mapped[str] = mapped_column(CITEXT)
    full_name: Mapped[str] = mapped_column(Text)
    role: Mapped[TeamRole] = mapped_column(pg_enum(TeamRole, "team_role"))
    token_hash: Mapped[str] = mapped_column(Text)
    status: Mapped[InvitationStatus] = mapped_column(pg_enum(InvitationStatus, "invitation_status"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
