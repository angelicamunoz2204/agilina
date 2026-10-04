import os

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import elevenlabs, google, openai, silero

server = AgentServer()

INSTRUCCIONES = (
    "Eres Agilina, una facilitadora de prueba. Responde siempre en español, "
    "en una sola frase corta, resumiendo lo que acaba de decir el participante."
)


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(
            base_url=os.environ["WHISPER_BASE_URL"],
            api_key="no-se-usa",  # speaches no valida la llave
            model=os.environ.get("WHISPER_MODEL", "Systran/faster-whisper-small"),
            language="es",
        ),
        llm=google.LLM(
            api_key=os.environ["GOOGLE_API_KEY"],
            model=os.environ["GEMINI_MODEL"],
        ),
        tts=elevenlabs.TTS(
            api_key=os.environ["ELEVEN_API_KEY"],
            voice_id=os.environ["ELEVEN_VOICE_ID"],
            model=os.environ.get("ELEVEN_MODEL", "eleven_v4_turbo"),
        ),
    )
    await session.start(room=ctx.room, agent=Agent(instructions=INSTRUCCIONES))
    await session.say("Hola equipo, soy Agilina. Cuéntenme algo y les respondo.")


if __name__ == "__main__":
    agents.cli.run_app(server)
