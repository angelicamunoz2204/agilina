"""Every response carries the identifier of its request."""

import logging

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agilina_api.shared.infrastructure.logging_setup import RequestIdFilter
from agilina_api.shared.presentation.http.request_id import RequestIdMiddleware

logger = logging.getLogger("tests.request_id")


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/")
    async def index() -> dict[str, str]:
        return {}

    return app


async def _get(headers: dict[str, str] | None = None):
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://tests") as client:
        return await client.get("/", headers=headers)


async def test_a_response_without_a_sent_identifier_gets_a_new_one():
    first, second = await _get(), await _get()

    assert len(first.headers["x-request-id"]) == 16
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


async def test_a_well_formed_identifier_from_the_caller_is_kept():
    response = await _get({"X-Request-ID": "web-1234-abcd"})

    assert response.headers["x-request-id"] == "web-1234-abcd"


async def test_an_identifier_that_could_forge_a_log_line_is_replaced():
    response = await _get({"X-Request-ID": "x\nERROR fake line"})

    assert "fake" not in response.headers["x-request-id"]


async def test_log_records_carry_the_identifier_of_the_request_that_caused_them():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    seen: list[str] = []
    capture = logging.Handler()
    capture.emit = lambda record: seen.append(record.request_id)  # type: ignore[method-assign]
    capture.addFilter(RequestIdFilter())
    logger.addHandler(capture)
    logger.setLevel(logging.INFO)

    @app.get("/")
    async def index() -> None:
        logger.info("inside")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tests") as client:
        response = await client.get("/", headers={"X-Request-ID": "web-1234-abcd"})
    logger.info("outside")
    logger.removeHandler(capture)

    assert response.headers["x-request-id"] == "web-1234-abcd"
    assert seen == ["web-1234-abcd", "-"]


async def test_what_is_not_an_http_request_goes_through_untouched():
    seen: list[str] = []

    async def inner(scope, receive, send) -> None:
        seen.append(scope["type"])

    await RequestIdMiddleware(inner)({"type": "lifespan"}, None, None)

    assert seen == ["lifespan"]
