from pydantic import BaseModel


class ServiceStatusResponse(BaseModel):
    service: str = "agilina-api"
    version: str
    environment: str
    status: str
