"""Worker adapter against the Agilina API.

It authenticates with the worker service account in Keycloak (client
credentials) and retries if the API does not respond: losing the result of a
ceremony because the API restarted is not acceptable.
"""

import asyncio
from collections.abc import Callable

import httpx

from agilina_agent.application.ports import AgilinaApi
from agilina_agent.infrastructure.logging_setup import get_logger
from agilina_shared.contract import CeremonyContext, CeremonyResult

logger = get_logger(__name__)

RETRIES = 3
DELAY_BETWEEN_RETRIES = 2.0


class HttpAgilinaApi(AgilinaApi):
    def __init__(
        self,
        base_url: str,
        get_token: Callable[[], str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._get_token = get_token
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0))

    def _headers(self) -> dict[str, str]:
        if self._get_token is None:
            return {}
        return {"Authorization": f"Bearer {self._get_token()}"}

    async def get_context(self, ceremony_id: str) -> CeremonyContext:
        response = await self._client.get(
            f"{self._base_url}/v1/ceremonies/{ceremony_id}/context",
            headers=self._headers(),
        )
        response.raise_for_status()
        return CeremonyContext.model_validate(response.json())

    async def deliver_result(self, result: CeremonyResult) -> None:
        last_error: Exception | None = None

        for attempt in range(1, RETRIES + 1):
            try:
                response = await self._client.post(
                    f"{self._base_url}/v1/ceremonies/{result.ceremony_id}/result",
                    content=result.model_dump_json(),
                    headers={"Content-Type": "application/json", **self._headers()},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                # A 4xx is a result the API rejects: retrying will not fix it.
                # Only what may be transient is retried.
                if error.response.status_code < 500:
                    raise
                last_error = error
            except httpx.TransportError as error:
                last_error = error
            else:
                logger.info("Result of ceremony %s delivered", result.ceremony_id)
                return

            logger.warning(
                "Attempt %s of %s to deliver the result failed: %s",
                attempt,
                RETRIES,
                last_error,
            )
            if attempt < RETRIES:
                await asyncio.sleep(DELAY_BETWEEN_RETRIES * attempt)

        raise RuntimeError("Could not deliver the result to the API") from last_error

    async def close(self) -> None:
        await self._client.aclose()
