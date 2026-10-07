from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """The token travels in the body, never in the URL: a URL ends up in logs."""

    token: str = Field(max_length=200)
