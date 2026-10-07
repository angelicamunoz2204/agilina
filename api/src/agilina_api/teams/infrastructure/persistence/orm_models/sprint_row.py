from datetime import date
from uuid import UUID

from sqlalchemy import Date, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.database.types import pg_enum
from agilina_api.teams.domain.sprint import SprintStatus


class SprintRow(Base):
    __tablename__ = "sprint"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[SprintStatus] = mapped_column(pg_enum(SprintStatus, "sprint_status"))
