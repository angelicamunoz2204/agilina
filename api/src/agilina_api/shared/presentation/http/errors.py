"""The single error handler of the API and the error format every context answers with.

Each context brings its own table of ``ErrorMapping``s and the composition root registers
them all here. The domain knows nothing about status codes: the tables are the only place
that says that an expired link is a ``410`` or a refused password a ``422``.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agilina_api.shared.application.access import NotATeamMemberError, NotAuthenticatedError
from agilina_api.shared.application.ports import MailDeliveryError


class ErrorResponse(BaseModel):
    """Every failure answers with a stable ``code`` the web turns into a message in the
    person's language; ``detail`` is for developers."""

    code: str
    detail: str
    reasons: list[str] | None = None


@dataclass(frozen=True)
class ErrorMapping:
    """How one exception type becomes an HTTP response.

    ``reasons`` extracts stable codes from the error when the interface needs more than the
    ``code``; ``headers`` are sent along with the response.
    """

    error_type: type[Exception]
    status: int
    code: str
    reasons: Callable[[Exception], list[str]] | None = None
    headers: Mapping[str, str] | None = None


SHARED_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(
        NotAuthenticatedError, 401, "not_authenticated", headers={"WWW-Authenticate": "Bearer"}
    ),
    # The same answer whether the team is someone else's, the user was removed from it or
    # it does not exist: a 404 for the last one would let anybody enumerate teams.
    ErrorMapping(NotATeamMemberError, 403, "not_a_team_member"),
    ErrorMapping(MailDeliveryError, 502, "mail_unavailable"),
)


def error_response(
    status: int,
    code: str,
    detail: str,
    reasons: list[str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(code=code, detail=detail, reasons=reasons)
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        headers={**(headers or {}), "Cache-Control": "no-store"},
    )


def register_error_handlers(app: FastAPI, mappings: Iterable[ErrorMapping]) -> None:
    for mapping in mappings:

        async def handle(
            request: Request, error: Exception, mapping: ErrorMapping = mapping
        ) -> JSONResponse:
            reasons = mapping.reasons(error) if mapping.reasons is not None else None
            # The detail is generic on purpose: the messages of the errors name people and
            # invitations, and the response must not.
            return error_response(
                mapping.status,
                mapping.code,
                mapping.code.replace("_", " "),
                reasons,
                mapping.headers,
            )

        app.add_exception_handler(mapping.error_type, handle)
