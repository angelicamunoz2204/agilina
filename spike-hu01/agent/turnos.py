"""Cierre manual del turno (diseño decidido para HU-26) y registro de tiempos del spike HU-01.

Por qué la espera la controla el agente y no commit_user_turn(transcript_timeout=...):
en livekit-agents 1.8.4, si la última transcripción final llegó hace más de 0,5 s, commit_user_turn espera la
*siguiente* transcripción hasta transcript_timeout; con el micrófono activo no inyecta silencio. Con nuestro STT sin
streaming, si no queda nada en vuelo esa transcripción nunca llega y el commit tarda el timeout completo; si llegó una
hace menos de 0,5 s no espera aunque otro segmento siga en Whisper. Aquí el agente espera (1) a que el VAD dé por
terminada la voz y (2) a que no queden segmentos en vuelo, y luego confirma con transcript_timeout=0.

Un segmento cuenta como "en vuelo" desde el fin de voz del VAD de la sesión (user_state speaking → listening) hasta
que Whisper responde. StreamAdapter usa otro flujo del mismo VAD y procesa los segmentos en serie, así que el i-ésimo
fin de voz se empareja con la i-ésima petición: en_vuelo = max(fines de voz, peticiones iniciadas) - respondidas.

Todos los eventos se registran en el logger "agilina.turnos" con t_ms (epoch en milisegundos).
"""

import asyncio
import logging
import time

from livekit import rtc
from livekit.agents import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, APIConnectOptions, NotGivenOr
from livekit.plugins import openai

logger = logging.getLogger("agilina.turnos")
SONDEO_S = 0.01  # resolución de la espera (10 ms)


def ahora_ms() -> int:
    return int(time.time() * 1000)


class SeguimientoSegmentos:
    def __init__(self) -> None:
        self.fines_voz_ms: list[int] = []
        self.inicios = 0
        self.respondidas = 0
        self.max_en_vuelo = 0

    @property
    def en_vuelo(self) -> int:
        return max(len(self.fines_voz_ms), self.inicios) - self.respondidas

    def _actualizar_max(self) -> None:
        self.max_en_vuelo = max(self.max_en_vuelo, self.en_vuelo)

    def fin_de_voz(self) -> None:
        self.fines_voz_ms.append(ahora_ms())
        self._actualizar_max()
        logger.info(
            "vad_fin_voz",
            extra={"t_ms": self.fines_voz_ms[-1], "segmento": len(self.fines_voz_ms), "en_vuelo": self.en_vuelo},
        )

    def peticion_inicia(self, audio_s: float) -> dict:
        self.inicios += 1
        t = ahora_ms()
        i = self.inicios
        fin_voz = self.fines_voz_ms[i - 1] if i <= len(self.fines_voz_ms) else None
        self._actualizar_max()
        seg = {"segmento": i, "t_inicio_ms": t, "audio_s": round(audio_s, 3)}
        logger.info(
            "whisper_peticion",
            extra={
                "t_ms": t,
                "segmento": i,
                "audio_s": round(audio_s, 3),
                # negativo si el VAD del adaptador terminó antes que el de la sesión
                "espera_en_cola_ms": t - fin_voz if fin_voz is not None else None,
                "en_vuelo": self.en_vuelo,
                "max_en_vuelo": self.max_en_vuelo,
            },
        )
        return seg

    def peticion_termina(self, seg: dict, texto: str | None) -> None:
        self.respondidas += 1
        t = ahora_ms()
        stt_ms = t - seg["t_inicio_ms"]
        logger.info(
            "whisper_respuesta",
            extra={
                "t_ms": t,
                "segmento": seg["segmento"],
                "audio_s": seg["audio_s"],
                "stt_ms": stt_ms,
                "rtf": round(stt_ms / 1000 / seg["audio_s"], 3) if seg["audio_s"] else None,
                "error": texto is None,
                "texto": texto or "",
                "en_vuelo": self.en_vuelo,
            },
        )


class WhisperSTT(openai.STT):
    """openai.STT que avisa al seguimiento cuando cada segmento sale hacia Whisper y cuando vuelve."""

    def __init__(self, *args, seguimiento: SeguimientoSegmentos, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._seguimiento = seguimiento

    async def recognize(
        self,
        buffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ):
        frames = buffer if isinstance(buffer, list) else [buffer]
        seg = self._seguimiento.peticion_inicia(sum(f.duration for f in frames))
        texto = None
        try:
            ev = await super().recognize(buffer, language=language, conn_options=conn_options)
            texto = ev.alternatives[0].text if ev.alternatives else ""
            return ev
        finally:
            self._seguimiento.peticion_termina(seg, texto)


class CierreManual:
    """Atiende la orden "terminar_turno" (RPC) y confirma el turno cuando ya no queda nada por transcribir."""

    def __init__(self, session, seguimiento: SeguimientoSegmentos, espera_max_s: float) -> None:
        self._session = session
        self._seg = seguimiento
        self._espera_max_s = espera_max_s
        self._tareas: set[asyncio.Task] = set()

    async def al_recibir_rpc(self, data: rtc.RpcInvocationData) -> str:
        t_boton = ahora_ms()
        logger.info(
            "boton_recibido",
            extra={
                "t_ms": t_boton,
                "caller_identity": data.caller_identity,
                "user_state": self._session.user_state,
                "en_vuelo": self._seg.en_vuelo,
            },
        )
        tarea = asyncio.create_task(self._cerrar(t_boton))
        self._tareas.add(tarea)
        tarea.add_done_callback(self._tareas.discard)
        return "ok"

    async def _esperar(self, condicion, limite: float) -> int:
        inicio = time.time()
        while condicion() and time.time() < limite:
            await asyncio.sleep(SONDEO_S)
        return int((time.time() - inicio) * 1000)

    async def _cerrar(self, t_boton: int) -> None:
        limite = t_boton / 1000 + self._espera_max_s
        espera_vad_ms = await self._esperar(lambda: self._session.user_state == "speaking", limite)
        espera_whisper_ms = await self._esperar(lambda: self._seg.en_vuelo > 0, limite)
        hablando = self._session.user_state == "speaking"
        timeout = hablando or self._seg.en_vuelo > 0
        t_commit = ahora_ms()
        logger.info(
            "espera_terminada",
            extra={
                "t_ms": t_commit,
                "espera_vad_ms": espera_vad_ms,
                "espera_whisper_ms": espera_whisper_ms,
                "espera_total_ms": t_commit - t_boton,
                "timeout": timeout,
                "timeout_por": ("vad" if hablando else "whisper") if timeout else None,
                "en_vuelo_restante": self._seg.en_vuelo,
                "espera_max_s": self._espera_max_s,
            },
        )
        if timeout:
            logger.warning("espera_transcripcion_timeout", extra={"t_ms": t_commit, "espera_max_s": self._espera_max_s})
        logger.info("commit_invocado", extra={"t_ms": t_commit})
        transcripcion = await self._session.commit_user_turn(transcript_timeout=0.0, stt_flush_duration=0.0)
        t_conf = ahora_ms()
        logger.info(
            "turno_confirmado",
            extra={
                "t_ms": t_conf,
                "boton_a_confirmado_ms": t_conf - t_boton,
                "commit_a_confirmado_ms": t_conf - t_commit,
                "max_en_vuelo": self._seg.max_en_vuelo,
                "transcripcion": transcripcion,
            },
        )
