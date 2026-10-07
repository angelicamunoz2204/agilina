from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Text, Uuid
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from agilina_api.shared.infrastructure.database.base import Base


class AppUserRow(Base):
    __tablename__ = "app_user"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    keycloak_subject: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(CITEXT)
    full_name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
