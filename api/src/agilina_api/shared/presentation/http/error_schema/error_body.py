from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    status: int = Field(examples=[422])
    code: str = Field(examples=["validation_error"])
    message: str = Field(examples=["The request is not valid."])
    details: dict[str, Any] | None = None
    request_id: str = Field(examples=["c1b9f0a2e47d4c1f"])
