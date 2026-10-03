"""Speech synthesis adapters.

The real implementation arrives with the story that gives Agilina a voice; the
recording synthesizer exists from now on so the whole ceremony can run locally
without spending minutes of a paid service.
"""

from agilina_agent.application.ports import SpeechSynthesizer
from agilina_agent.infrastructure.logging_setup import get_logger
from agilina_shared.enums import Language

logger = get_logger(__name__)


class ElevenLabsSynthesizer(SpeechSynthesizer):
    def __init__(self, api_key: str, voice_by_language: dict[Language, str]) -> None:
        self._api_key = api_key
        self._voice_by_language = voice_by_language

    async def synthesize(self, text: str, language: Language) -> bytes:
        raise NotImplementedError(
            "Speech synthesis pending: HU-23. The port and the recording adapter "
            "already allow exercising the facilitation machine."
        )


class RecordingSynthesizer(SpeechSynthesizer):
    """Records what Agilina would say instead of synthesizing it.

    It is what lets a ceremony run end to end locally, and also what the tests
    use.
    """

    def __init__(self) -> None:
        self.spoken: list[tuple[Language, str]] = []

    async def synthesize(self, text: str, language: Language) -> bytes:
        self.spoken.append((language, text))
        logger.info("[simulated voice · %s] %s", language.value, text)
        return b""
