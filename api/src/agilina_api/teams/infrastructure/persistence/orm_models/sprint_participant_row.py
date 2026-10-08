from uuid import UUID

from sqlalchemy import Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base


class SprintParticipantRow(Base):
    __tablename__ = "sprint_participant"

    sprint_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    team_id: Mapped[UUID] = mapped_column(Uuid)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    turn_order: Mapped[int] = mapped_column(Integer)
