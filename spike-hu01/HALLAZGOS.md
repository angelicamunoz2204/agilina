# Spike HU-01 — Hallazgos

## HU-01.4 · Cliente Angular (cumplida)
- Versiones: Angular 22.2, TypeScript 6.0.2, livekit-client 2.22.3.
- TypeScript 6 activa `strict` por defecto y Angular ya no lo declara en tsconfig.
  Verificado: el build rechaza `any` implícito y `null` en `string`.
  Recomendación: declarar `"strict": true` explícito en el proyecto real.
- livekit-client lleva el bundle inicial a ~758 kB (presupuesto de Angular: 500 kB).
  Recomendación: cargar la pantalla de sala con lazy loading.
- El audio solo se reproduce si la conexión ocurre dentro de un clic (política de autoplay).
- El micrófono solo funciona en localhost o HTTPS: cada participante necesita su cliente
  local o un despliegue con HTTPS.
- Angular 22 es zoneless por defecto: los eventos de LiveKit se reflejan en la vista mediante signals.

## Paso 10 · Agente mínimo con TTS
- Versiones: livekit-agents 1.8.4, livekit-plugins-elevenlabs 1.8.4, Python 3.12.
- Con despacho automático, el agente entra a toda sala nueva del proyecto: un trabajo por sala.
  Saluda una sola vez al arrancar; quienes entran después no disparan un nuevo saludo.
- ElevenLabs funciona desde el plugin con el modelo eleven_v4_turbo.
- Segunda prueba en sala con gemini-3.8-flash: 504 (timeout de ~11 s) y luego 503. En el nivel
  gratuito el modelo más reciente no es confiable; se valida la cadena con gemini-3.5-flash-lite.
- Whisper small en CPU: "Keycloak" → "kicklock" y "Hoy sigo" → "voy seguro". Errores de palabras
  comunes, no solo de términos técnicos: revisar con el modelo grande en GPU.
- Transcripción en sala: 4,20 s desde el fin del habla (incluye carga en frío de 1,11 s; faltaba WHISPER__TTL).
- Cadena completa funcionando con gemini-3.5-flash-lite: transcripción → resumen → voz en la sala.
  Tiempos en CPU (solo referencia): transcripción 5,60 s; respuesta registrada ~8,1 s después del turno.
  "Keycloak" volvió a transcribirse como "KeyClub", y Gemini repitió el error en el resumen:
  los errores del STT se propagan al LLM sin corrección.
- Desglose de los 5,60 s: ~0,8 s VAD + 2,38 s carga del modelo + 2,42 s transcripción (6,4 s de audio).
  WHISPER__TTL=-1 evita descargar el modelo, pero no lo carga al arrancar: hace falta precargarlo
  (PRELOAD_MODELS). Sin carga en frío, la transcripción en CPU queda en ~3,2 s.
- Cargar Silero VAD en el entrypoint bloquea el agente ~160 ms al iniciar cada sesión;
  en producción conviene cargarlo una vez por proceso.
- Línea base en CPU sin carga en frío (modelo small precargado): transcripción en 3,53 s desde el fin del habla.
- "agente" se transcribió como "de la gente" (error fonético comprensible).
- Gemini agregó contenido inexistente al resumir ("con datos reales"): el LLM no solo propaga errores
  del STT, también inventa detalles. Para el resumen de cierre: instrucciones estrictas de fidelidad
  y validación contra la transcripción (insumo para la HU del resumen).
- Segunda prueba sin carga en frío: transcripción exacta ("endpoint", "API"), 3,41 s; resumen fiel.
  Línea base en CPU (small): 3,4–3,5 s desde el fin del habla.
- Si alguien entra a la sala antes de que LiveKit cierre la anterior, no se despacha un agente nuevo.
  Protocolo de medición: una sala nueva por sesión de pruebas.
