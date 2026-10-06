"""The single error handler: how a mapped exception becomes the common ``ErrorResponse``."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agilina_api.shared.presentation.http.errors import (
    SHARED_ERRORS,
    ErrorMapping,
    register_error_handlers,
)


class _RefusedError(Exception):
    """An error a context would raise; its message names a person."""


class _ExplainedError(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("Refused for julian@example.test")
        self.reasons = reasons


def _reasons_of(error: Exception) -> list[str]:
    assert isinstance(error, _ExplainedError)
    return error.reasons


def _app(*mappings: ErrorMapping) -> FastAPI:
    """A minimal application whose routes raise the errors under test."""
    app = FastAPI()
    register_error_handlers(app, mappings)

    @app.get("/refused")
    async def refused() -> None:
        raise _RefusedError("Julián Torres cannot do that")

    @app.get("/explained")
    async def explained() -> None:
        raise _ExplainedError(["min_length", "digits"])

    return app


async def _get(app: FastAPI, path: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tests") as client:
        return await client.get(path)


async def test_a_mapped_error_answers_with_its_status_and_code():
    response = await _get(_app(ErrorMapping(_RefusedError, 409, "refused_here")), "/refused")

    assert response.status_code == 409
    assert response.json()["code"] == "refused_here"


async def test_the_detail_is_generic_and_never_the_exception_message():
    response = await _get(_app(ErrorMapping(_RefusedError, 409, "refused_here")), "/refused")

    assert response.json() == {"code": "refused_here", "detail": "refused here"}
    assert "Julián" not in response.text


async def test_error_responses_are_not_cached():
    response = await _get(
        _app(
            ErrorMapping(
                _RefusedError, 409, "refused_here", headers={"Cache-Control": "max-age=60"}
            )
        ),
        "/refused",
    )

    assert response.headers["cache-control"] == "no-store"


async def test_reasons_are_included_only_when_the_mapping_extracts_them():
    with_reasons = await _get(
        _app(ErrorMapping(_ExplainedError, 422, "explained", reasons=_reasons_of)), "/explained"
    )
    without_reasons = await _get(
        _app(ErrorMapping(_ExplainedError, 422, "explained")), "/explained"
    )

    assert with_reasons.json() == {
        "code": "explained",
        "detail": "explained",
        "reasons": ["min_length", "digits"],
    }
    assert without_reasons.json() == {"code": "explained", "detail": "explained"}
    assert "julian" not in with_reasons.text.lower()


async def test_mapped_headers_are_sent():
    response = await _get(
        _app(
            ErrorMapping(_RefusedError, 401, "refused_here", headers={"WWW-Authenticate": "Bearer"})
        ),
        "/refused",
    )

    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    ("code", "status"),
    [("not_authenticated", 401), ("not_a_team_member", 403), ("mail_unavailable", 502)],
)
def test_the_shared_table_maps_the_errors_every_context_can_raise(code, status):
    assert {(m.code, m.status) for m in SHARED_ERRORS} >= {(code, status)}
