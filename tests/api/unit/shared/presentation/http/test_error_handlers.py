"""The handlers: whatever fails, the answer has the one error body."""

import logging

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from agilina_api.shared.presentation.http.api_error import ApiError, ApiException, SharedErrors
from agilina_api.shared.presentation.http.error_handlers import (
    SHARED_ERRORS,
    ErrorMapping,
    register_error_handlers,
)
from agilina_api.shared.presentation.http.request_id import RequestIdMiddleware

REFUSED = ApiError(409, "refused_here", "It was refused.")
SECRET = "Sup3rSecret!-do-not-echo"


class _RefusedError(Exception):
    """An error a context would raise; its message names a person."""


class _ExplainedError(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("Refused for julian@example.test")
        self.reasons = reasons


def _reasons_of(error: Exception) -> dict:
    assert isinstance(error, _ExplainedError)
    return {"reasons": error.reasons}


class _Body(BaseModel):
    password: str = Field(max_length=5)


def _app(*mappings: ErrorMapping) -> FastAPI:
    """A minimal application whose routes fail in every way the handlers cover."""
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app, mappings)

    @app.get("/refused")
    async def refused() -> None:
        raise _RefusedError("Julián Torres cannot do that")

    @app.get("/explained")
    async def explained() -> None:
        raise _ExplainedError(["min_length", "digits"])

    @app.get("/api-exception")
    async def api_exception() -> None:
        raise ApiException(REFUSED, {"hint": "x"})

    @app.post("/body")
    async def body(payload: _Body) -> None:
        return None

    @app.get("/teapot")
    async def teapot() -> None:
        raise HTTPException(status_code=418, detail="I am a teapot")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("database password is hunter2")

    return app


async def _call(app: FastAPI, method: str, path: str, **kwargs):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://tests") as client:
        return await client.request(method, path, **kwargs)


def _mapped(**kwargs) -> FastAPI:
    return _app(ErrorMapping(_RefusedError, REFUSED, **kwargs))


async def test_a_mapped_error_answers_with_the_envelope_of_its_catalog_entry():
    response = await _call(_mapped(), "GET", "/refused")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["status"] == 409 and error["code"] == "refused_here"
    assert error["message"] == "It was refused."
    assert set(error) == {"status", "code", "message", "request_id"}


async def test_the_message_is_the_catalogs_and_never_the_exception_message():
    response = await _call(_mapped(), "GET", "/refused")

    assert "Julián" not in response.text


async def test_error_responses_are_not_cached():
    response = await _call(_mapped(), "GET", "/refused")

    assert response.headers["cache-control"] == "no-store"


async def test_details_are_included_only_when_the_mapping_extracts_them():
    explained = ApiError(422, "explained", "Explained.")
    with_details = await _call(
        _app(ErrorMapping(_ExplainedError, explained, details=_reasons_of)), "GET", "/explained"
    )
    without = await _call(_app(ErrorMapping(_ExplainedError, explained)), "GET", "/explained")

    assert with_details.json()["error"]["details"] == {"reasons": ["min_length", "digits"]}
    assert "details" not in without.json()["error"]
    assert "julian" not in with_details.text.lower()


async def test_the_headers_of_the_catalog_entry_are_sent():
    response = await _call(
        _app(ErrorMapping(_RefusedError, SharedErrors.NOT_AUTHENTICATED)), "GET", "/refused"
    )

    assert response.headers["www-authenticate"] == "Bearer"


async def test_an_api_exception_answers_with_its_entry_and_details():
    response = await _call(_app(), "GET", "/api-exception")

    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"hint": "x"}


async def test_a_body_that_fails_validation_names_the_field_and_the_reason_not_the_value():
    response = await _call(_app(), "POST", "/body", json={"password": SECRET})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"]["fields"] == [{"field": "body.password", "reason": "string_too_long"}]
    assert SECRET not in response.text


async def test_a_route_that_does_not_exist_is_a_404_in_the_same_envelope():
    response = await _call(_app(), "GET", "/nowhere")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_a_method_that_is_not_allowed_is_a_405_in_the_same_envelope():
    response = await _call(_app(), "DELETE", "/body")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


async def test_a_status_without_an_entry_keeps_its_number_under_a_derived_code():
    response = await _call(_app(), "GET", "/teapot")

    assert response.status_code == 418
    assert response.json()["error"]["code"] == "http_418"
    assert "teapot" not in response.text


async def test_an_unexpected_error_is_a_500_that_leaks_nothing_and_is_logged(caplog):
    with caplog.at_level(logging.ERROR):
        response = await _call(_app(), "GET", "/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in response.text
    assert "hunter2" in caplog.text


async def test_every_failure_has_the_same_shape():
    app = _mapped()
    answers = [
        await _call(app, "GET", "/refused"),
        await _call(app, "GET", "/api-exception"),
        await _call(app, "POST", "/body", json={}),
        await _call(app, "GET", "/nowhere"),
        await _call(app, "DELETE", "/body"),
        await _call(app, "GET", "/boom"),
    ]

    for response in answers:
        body = response.json()
        assert list(body) == ["error"]
        assert {"status", "code", "message", "request_id"} <= set(body["error"])
        assert body["error"]["status"] == response.status_code
        assert body["error"]["request_id"] == response.headers["x-request-id"]


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("tenant_required", 400),
        ("tenant_not_found", 404),
        ("not_authenticated", 401),
        ("not_a_team_member", 403),
        ("mail_unavailable", 502),
    ],
)
def test_the_shared_table_maps_the_errors_every_context_can_raise(code, status):
    assert {(m.error.code, m.error.status) for m in SHARED_ERRORS} >= {(code, status)}
