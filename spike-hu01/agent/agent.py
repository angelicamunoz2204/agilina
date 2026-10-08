import asyncio
import os

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, StopResponse
from livekit.agents.voice import room_io
from livekit.plugins import elevenlabs, google, silero

from metricas import RegistroMetricas
from turnos import CierreManual, SeguimientoSegmentos, WhisperSTT, ahora_ms, logger as log_turnos

server = AgentServer()

USAR_LLM = os.environ.get("USAR_LLM") == "1"
RESPUESTA_FIJA = "Gracias, quedó anotado."  # Plantilla, como en la ceremonia real (AD-19)
MIN_PALABRAS = 3  # Solo en modo stt: turnos más cortos se ignoran (p. ej. un "Gracias." alucinado por Whisper)
# manual (por defecto, diseño de HU-26): el participante cierra su turno con "Terminar turno" (RPC terminar_turno).
# stt: el turno se cierra cuando llega la transcripción y pasa al menos `min_delay` desde el fin de la voz.
MODO_TURNO = os.environ.get("MODO_TURNO", "manual")
ESPERA_TRANSCRIPCION_S = float(os.environ.get("ESPERA_TRANSCRIPCION_S", "10"))
TURNOS = (
    {"turn_detection": "manual"}
    if MODO_TURNO == "manual"
    else {"turn_detection": "stt", "endpointing": {"min_delay": 1.0}}
)
# Silero descarta el audio de un segmento que supere max_buffered_speech (60 s por defecto en 1.8.4).
VAD_MAX_BUFFERED_SPEECH_S = os.environ.get("VAD_MAX_BUFFERED_SPEECH_S", "")
INSTRUCCIONES = (
    "Eres Agilina, una facilitadora de prueba. Responde siempre en español, "
    "en una sola frase corta, resumiendo lo que acaba de decir el participante."
)


class Agilina(Agent):
    def __init__(self, ceder_turno_tras, registro: RegistroMetricas) -> None:
        super().__init__(instructions=INSTRUCCIONES)
        self._ceder_turno_tras = ceder_turno_tras
        self._registro = registro

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        texto = new_message.text_content or ""
        if MODO_TURNO != "manual" and not USAR_LLM and len(texto.split()) < MIN_PALABRAS:
            self._registro.descartar_turno()
            raise StopResponse()  # Texto vacío o casi vacío: no se responde ni se cede el turno.
        hablante = self.session.room_io.linked_participant
        # new_message.metrics ya trae los tiempos del turno (transcription_delay, stopped_speaking_at, ...).
        self._registro.iniciar_turno(hablante.identity if hablante else "", texto, new_message.metrics)
        if USAR_LLM:
            return  # Responde el LLM; el turno se cede al terminar esa respuesta.
        respuesta = self.session.say(RESPUESTA_FIJA)
        self._ceder_turno_tras(respuesta)
        raise StopResponse()  # Sin LLM: no generar respuesta adicional.


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    llm = (
        google.LLM(api_key=os.environ["GOOGLE_API_KEY"], model=os.environ["GEMINI_MODEL"])
        if USAR_LLM
        else None
    )
    whisper_prompt = os.environ.get("WHISPER_PROMPT", "")
    registro = RegistroMetricas(
        sala=ctx.room.name,
        carpeta=os.environ.get("METRICAS_DIR", "/metrics"),
        contexto={
            "entorno": os.environ.get("ENTORNO", "desconocido"),
            "whisper_model": os.environ.get("WHISPER_MODEL", "Systran/faster-whisper-small"),
            "prompt_activo": "sí" if whisper_prompt else "no",
            "eleven_model": os.environ.get("ELEVEN_MODEL", "eleven_v4_turbo"),
            "usar_llm": "1" if USAR_LLM else "0",
        },
    )
    seguimiento = SeguimientoSegmentos()
    stt = WhisperSTT(
        seguimiento=seguimiento,
        base_url=os.environ["WHISPER_BASE_URL"],
        api_key="no-se-usa",  # speaches no valida la llave
        model=os.environ.get("WHISPER_MODEL", "Systran/faster-whisper-small"),
        language="es",
        # Vocabulario para Whisper (initial_prompt en speaches). Vacío = sin prompt: el plugin lo omite.
        prompt=whisper_prompt,
    )
    tts = elevenlabs.TTS(
        api_key=os.environ["ELEVEN_API_KEY"],
        voice_id=os.environ["ELEVEN_VOICE_ID"],
        model=os.environ.get("ELEVEN_MODEL", "eleven_v4_turbo"),
    )
    # Métricas de componente (duración de cada petición a Whisper, caracteres enviados a ElevenLabs).
    # En la sesión el evento metrics_collected está deprecado; en los componentes no.
    stt.on("metrics_collected", registro.al_medir_stt)
    tts.on("metrics_collected", registro.al_medir_tts)
    vad = (
        silero.VAD.load(max_buffered_speech=float(VAD_MAX_BUFFERED_SPEECH_S))
        if VAD_MAX_BUFFERED_SPEECH_S
        else silero.VAD.load()
    )
    session = AgentSession(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=tts,
        turn_handling=TURNOS,
    )
    session.on("conversation_item_added", lambda ev: registro.al_agregar_mensaje(ev.item))

    @session.on("user_state_changed")
    def al_cambiar_usuario(ev) -> None:
        if ev.old_state == "speaking" and ev.new_state != "speaking":
            seguimiento.fin_de_voz()  # el segmento queda "en vuelo" hasta que Whisper responda

    @session.on("agent_state_changed")
    def al_cambiar_agente(ev) -> None:
        if ev.new_state == "speaking":
            log_turnos.info("agilina_habla", extra={"t_ms": ahora_ms()})
    tareas: set[asyncio.Task] = set()

    def siguiente_participante() -> str | None:
        humanos = list(ctx.room.remote_participants.keys())  # en orden de llegada
        if not humanos:
            return None
        actual = session.room_io.linked_participant
        if actual is None or actual.identity not in humanos:
            return humanos[0]
        return humanos[(humanos.index(actual.identity) + 1) % len(humanos)]

    async def ceder_turno(respuesta) -> None:
        await respuesta.wait_for_playout()
        siguiente = siguiente_participante()
        if siguiente:
            session.room_io.set_participant(siguiente)
            session.say(f"{siguiente}, tienes la palabra.")  # al agregarse este mensaje se cierra la fila
        else:
            registro.cerrar_turno()

    def ceder_turno_tras(respuesta) -> None:
        tarea = asyncio.create_task(ceder_turno(respuesta))
        tareas.add(tarea)
        tarea.add_done_callback(tareas.discard)

    if USAR_LLM:
        @session.on("speech_created")
        def al_crear_respuesta(ev) -> None:
            # Solo las respuestas del LLM ceden el turno; los anuncios (say) no.
            if ev.source == "generate_reply":
                ceder_turno_tras(ev.speech_handle)

    primero = await ctx.wait_for_participant()  # Así el saludo nombra a alguien y no a "equipo".
    await session.start(
        room=ctx.room,
        agent=Agilina(ceder_turno_tras, registro),
        room_options=room_io.RoomOptions(participant_identity=primero.identity),
    )
    log_turnos.info(
        "configuracion_turnos",
        extra={
            "t_ms": ahora_ms(),
            "modo_turno": MODO_TURNO,
            "espera_transcripcion_s": ESPERA_TRANSCRIPCION_S,
            "vad_max_buffered_speech_s": VAD_MAX_BUFFERED_SPEECH_S or "por defecto",
        },
    )
    if MODO_TURNO == "manual":
        # En el spike se acepta la orden de cualquier participante; restringirla a quien tiene la palabra es de HU-26.
        cierre = CierreManual(session, seguimiento, ESPERA_TRANSCRIPCION_S)
        ctx.room.local_participant.register_rpc_method("terminar_turno", cierre.al_recibir_rpc)
    session.say(f"Hola equipo, soy Agilina. {primero.identity}, tienes la palabra.")


if __name__ == "__main__":
    agents.cli.run_app(server)
