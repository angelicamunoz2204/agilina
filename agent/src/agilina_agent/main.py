"""Worker entry point and composition root.

    make agent     → registers the worker in LiveKit and waits for jobs

The worker opens an outbound connection to LiveKit and registers. When a
ceremony room is created, LiveKit offers the job over that connection and this
module launches the subprocess that joins the room as one more participant.

What is here is the skeleton that shows the life cycle: join the room,
announce itself and wait. Full facilitation arrives with the Release 1 and 2
stories; the logic that already exists lives in
``agilina_agent.domain.facilitation`` and is tested without a room or audio.
"""

from livekit.agents import JobContext, WorkerOptions, cli

from agilina_agent.infrastructure.logging_setup import configure_logging, get_logger
from agilina_agent.infrastructure.settings import get_settings
from agilina_agent.infrastructure.speech_synthesizers import RecordingSynthesizer
from agilina_agent.presentation.room_job import RoomJob

logger = get_logger(__name__)


async def entrypoint(ctx: JobContext) -> None:
    """Runs once per ceremony, in its own subprocess: wires the job here."""
    settings = get_settings()
    configure_logging(settings.log_level)

    job = RoomJob(
        synthesizer=RecordingSynthesizer(),
        default_language=settings.default_language,
    )
    await job.run(ctx)


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Registering the worker in %s", settings.livekit_url or "(not configured)")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    )


__all__ = ["entrypoint", "run"]

if __name__ == "__main__":
    run()
