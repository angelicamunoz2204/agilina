"""Registro de métricas por turno del spike HU-01: una fila por turno de usuario en metrics/<sala>.csv.

Fuentes (livekit-agents 1.8.4):
- ChatMessage.metrics del usuario (en on_user_turn_completed): started/stopped_speaking_at, transcription_delay.
  transcription_delay = llegada de la transcripción final - fin de la voz según el VAD (U1).
- ChatMessage.metrics de la respuesta (conversation_item_added): tts_node_ttfb (U2), llm_node_ttft,
  started_speaking_at (primer cuadro de audio entregado a la pista de la sala).
- Eventos metrics_collected de los objetos STT y TTS: STTMetrics.duration (petición a Whisper),
  STTMetrics.audio_duration, TTSMetrics.characters_count (= len(texto) enviado a ElevenLabs).

Tramos calculados (sin métrica oficial):
- espera_vad_s = u1_transcripcion_s - stt_s (stt_s = duración de la última petición del turno, la que entrega el texto).
- u3_aprox_s = started_speaking_at(respuesta) - stopped_speaking_at(usuario). Es la misma fórmula de e2e_latency,
  que LiveKit solo llena para respuestas del LLM; con say() (modo plantilla) se calcula aquí.
"""

import csv
import os
from datetime import datetime, timezone

COLUMNAS = [
    "sala", "participante", "hora_utc", "entorno", "whisper_model", "prompt_activo", "eleven_model", "usar_llm",
    "duracion_voz_s", "audio_stt_s", "segmentos_stt",
    "u1_transcripcion_s", "espera_vad_s", "stt_s",
    "llm_ttft_s", "u2_tts_ttfb_s", "u3_aprox_s", "caracteres_tts",
    "texto_transcrito", "texto_respondido",
]


def _num(valor):
    return "" if valor is None else f"{valor:.3f}"


class RegistroMetricas:
    def __init__(self, sala: str, contexto: dict, carpeta: str) -> None:
        self._contexto = {"sala": sala, **contexto}
        os.makedirs(carpeta, exist_ok=True)
        self._ruta = os.path.join(carpeta, f"{sala}.csv")
        self._stt_pendientes: list = []  # STTMetrics que llegan antes de cerrar el turno del usuario
        self._turno: dict | None = None

    # --- eventos de componentes ---
    def al_medir_stt(self, m) -> None:
        self._stt_pendientes.append(m)

    def al_medir_tts(self, m) -> None:
        if self._turno is not None:  # el saludo inicial no pertenece a ningún turno
            self._turno["caracteres"] += m.characters_count

    # --- ciclo del turno ---
    def descartar_turno(self) -> None:
        """Turno ignorado (p. ej. menos de 3 palabras): no genera fila."""
        self._stt_pendientes.clear()

    def iniciar_turno(self, participante: str, texto: str, metricas_usuario) -> None:
        if self._turno is not None:
            self.cerrar_turno()
        self._turno = {
            "participante": participante,
            "texto": texto,
            "usuario": metricas_usuario,  # dict vivo: LiveKit puede completarlo después
            "stt": self._stt_pendientes,
            "respuesta": None,
            "texto_respuesta": "",
            "caracteres": 0,
        }
        self._stt_pendientes = []

    def al_agregar_mensaje(self, item) -> None:
        """Primer mensaje de Agilina tras el turno = respuesta; el siguiente = anuncio de turno (cierra la fila)."""
        if self._turno is None or getattr(item, "role", None) != "assistant":
            return
        if self._turno["respuesta"] is None:
            self._turno["respuesta"] = item.metrics
            self._turno["texto_respuesta"] = item.text_content or ""
        else:
            self.cerrar_turno()

    def cerrar_turno(self) -> None:
        t, self._turno = self._turno, None
        if t is None:
            return
        u, r, stt = t["usuario"], t["respuesta"] or {}, t["stt"]
        inicio, fin = u.get("started_speaking_at"), u.get("stopped_speaking_at")
        u1 = u.get("transcription_delay")
        stt_s = stt[-1].duration if stt else None
        u3 = r["started_speaking_at"] - fin if fin is not None and "started_speaking_at" in r else None
        fila = {
            **self._contexto,
            "participante": t["participante"],
            "hora_utc": datetime.fromtimestamp(fin, tz=timezone.utc).isoformat(timespec="seconds") if fin else "",
            "duracion_voz_s": _num(fin - inicio if fin is not None and inicio is not None else None),
            "audio_stt_s": _num(sum(m.audio_duration for m in stt) if stt else None),
            "segmentos_stt": len(stt),
            "u1_transcripcion_s": _num(u1),
            "espera_vad_s": _num(u1 - stt_s if u1 is not None and stt_s is not None else None),
            "stt_s": _num(stt_s),
            "llm_ttft_s": _num(r.get("llm_node_ttft")),
            "u2_tts_ttfb_s": _num(r.get("tts_node_ttfb")),
            "u3_aprox_s": _num(u3),
            "caracteres_tts": t["caracteres"],
            "texto_transcrito": t["texto"],
            "texto_respondido": t["texto_respuesta"],
        }
        nuevo = not os.path.exists(self._ruta)
        with open(self._ruta, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            if nuevo:
                w.writeheader()
            w.writerow(fila)
