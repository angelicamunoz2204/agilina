"""LiveKit job: what the worker does once per ceremony, in its own subprocess.

This is the driving adapter of the worker. It receives its collaborators from
the composition root (``main.py``) and never imports the infrastructure layer.
"""

import logging

from livekit.agents import AutoSubscribe, JobContext

from agilina_agent.application.ports import SpeechSynthesizer
from agilina_shared.enums import Language

logger = logging.getLogger(__name__)


class RoomJob:
    def __init__(self, synthesizer: SpeechSynthesizer, default_language: Language) -> None:
        self._synthesizer = synthesizer
        self._default_language = default_language

    async def run(self, ctx: JobContext) -> None:
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Agilina joined room %s", ctx.room.name)

        # Waiting: Agilina is in the room but sends no audio to the transcription
        # service until someone starts the daily from the application.
        await self._synthesizer.synthesize(
            "Agilina is in the room and waiting.", self._default_language
        )
