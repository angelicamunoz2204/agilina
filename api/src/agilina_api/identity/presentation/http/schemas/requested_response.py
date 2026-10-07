from pydantic import BaseModel


class RequestedResponse(BaseModel):
    status: str = "requested"
