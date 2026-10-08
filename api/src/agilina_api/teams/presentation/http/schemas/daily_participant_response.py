from uuid import UUID

from pydantic import BaseModel, Field


class DailyParticipantResponse(BaseModel):
    user_id: UUID
    turn_order: int = Field(description="Position in the daily's round, from 1.")
