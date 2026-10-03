import os

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import elevenlabs

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        tts=elevenlabs.TTS(
            api_key=os.environ["ELEVEN_API_KEY"],
            voice_id=os.environ["ELEVEN_VOICE_ID"],
            model=os.environ.get("ELEVEN_MODEL", "eleven_v4_turbo"),
        ),
    )
    await session.start(room=ctx.room, agent=Agent(instructions="Agente de prueba del spike HU-01."))
    await session.say("Hola equipo, soy Agilina. Esta es una prueba del spike.")


if __name__ == "__main__":
    agents.cli.run_app(server)
