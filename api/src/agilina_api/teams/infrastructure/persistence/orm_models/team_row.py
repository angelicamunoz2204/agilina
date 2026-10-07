from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.database.types import pg_enum
from agilina_shared.enums import Language, OperationMode


class TeamRow(Base):
    __tablename__ = "team"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    mode: Mapped[OperationMode] = mapped_column(pg_enum(OperationMode, "team_mode"))
    language: Mapped[Language] = mapped_column(pg_enum(Language, "team_language"))
    created_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
