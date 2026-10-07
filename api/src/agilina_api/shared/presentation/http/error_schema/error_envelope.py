from pydantic import BaseModel

from agilina_api.shared.presentation.http.error_schema.error_body import ErrorBody


class ErrorEnvelope(BaseModel):
    error: ErrorBody
