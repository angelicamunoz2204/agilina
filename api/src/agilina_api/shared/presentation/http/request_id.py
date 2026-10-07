"""Gives every request an identifier, in the response and in every log line it causes."""

import re
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from agilina_api.shared.application.request_context import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
_VALID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestIdMiddleware:
    """Keeps the caller's identifier when it looks like one, and makes a new one otherwise.

    It also stores it in the ASGI scope: the handler of unexpected errors runs outside this
    middleware, where the context variable is already gone.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        sent = MutableHeaders(scope=scope).get(REQUEST_ID_HEADER, "")
        request_id = sent if _VALID.match(sent) else uuid.uuid4().hex[:16]
        scope["request_id"] = request_id
        token = request_id_var.set(request_id)

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)
