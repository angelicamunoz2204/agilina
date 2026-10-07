from pydantic import BaseModel, Field


class ActivateRequest(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(min_length=1, max_length=256)
    confirmation: str = Field(max_length=256)
