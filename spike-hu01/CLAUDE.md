# Spike HU-01 — Cadena de voz extremo a extremo (Agilina)

Agilina es un Scrum Master virtual por voz para Daily Stand-ups (tesis de maestría, Universidad del Valle).
Este directorio es el **prototipo del spike HU-01**: valida que la cadena audio → Whisper → (LLM) → ElevenLabs
funciona dentro de una sala de LiveKit y mide su latencia y costo.

Antes de trabajar, lee `README.md`, `UMBRALES.md` y `HALLAZGOS.md`.

## Reglas

- Prototipo **no productivo**. Vive en la rama `spike/hu-01-voz` y **nunca se fusiona a main**.
  El informe final sí va a main, en `docs/spikes/`, por PR.
- **Nunca** leas, muestres ni copies el contenido de `.env`. Las variables se documentan en `.env.example` sin valores.
- Todo corre en Docker. No instales Node, Python ni dependencias en el Mac.
- `UMBRALES.md` se fijó antes de medir: **no se modifica** para acomodar resultados.
- Cada hallazgo (versión, error, tiempo medido, decisión) se registra en `HALLAZGOS.md` en el momento,
  con datos concretos. Es la fuente para el informe.
- Antes de editar varios archivos o hacer un commit, explica brevemente qué vas a cambiar.
- Respuestas cortas y directas, en español.

## Commits

- Formato: `tipo(ámbito): descripción`, ámbitos permitidos: `api`, `agent`, `stt`, `web`, `infra`, `docs`.
- Pie obligatorio: `Refs: HU-01` (usar `git commit -m "..." -m "Refs: HU-01"`).
- **Un solo autor: Diego.** Sin `Co-Authored-By`, sin menciones a Claude ni líneas de atribución.
- Antes de cada commit, `git status` para confirmar que no entra `.env` ni CSV de métricas.
- No entran grabaciones de personas (voz real); la única excepción es `whisper/warmup.wav`, audio sintético de
  calentamiento sin datos personales.

## Estructura

```
spike-hu01/
├── CLAUDE.md, README.md, UMBRALES.md, HALLAZGOS.md
├── docker-compose.yml   # client, agent, whisper, whisper-warmup
├── docker-compose.gpu.yml # override para la instancia GPU (imagen CUDA, reserva de GPU, sin puerto 8000)
├── scripts/subir-gpu.sh # rsync a la instancia (sin client/ ni .env)
├── .env / .env.example
├── client/              # Angular 22 + livekit-client 2.22 (cliente mínimo de sala)
├── agent/               # Python 3.12 + livekit-agents 1.8.4 (agent.py, requirements.txt, Dockerfile)
└── whisper/warmup.wav   # audio corto para precalentar el modelo
```

## Servicios

| Servicio | Qué hace |
|---|---|
| `client` | Cliente Angular en http://localhost:4200. URL y token se pegan en pantalla. |
| `whisper` | speaches 0.8.3 (`/openapi.json` dice v0.8.2; API compatible con OpenAI) en :8000, imagen CPU fijada por digest. `WHISPER__TTL=-1`. |
| `whisper-warmup` | Espera a Whisper, descarga el modelo (`POST /v1/models/...`) y envía `warmup.wav` para cargarlo. speaches no tiene opción de precarga ni descarga sola. |
| `agent` | Worker de LiveKit. Arranca solo si `whisper-warmup` terminó bien. Despacho automático: entra a toda sala nueva. |

Variables de `.env`: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`, `GEMINI_MODEL`,
`USAR_LLM`, `ELEVEN_API_KEY`, `ELEVEN_VOICE_ID`, `ELEVEN_MODEL`, `WHISPER_BASE_URL`, `WHISPER_MODEL`.

- `USAR_LLM=0`: Agilina responde con plantilla ("Gracias, quedó anotado."), coherente con AD-19.
- `USAR_LLM=1`: responde Gemini (resumen en una frase).

## Comandos

```bash
docker compose up -d --build                      # compilar y levantar todo
docker compose up -d --force-recreate agent       # tras cambiar .env o agent.py
docker compose logs -f agent whisper              # seguir logs
docker compose logs whisper | grep -i "loaded in" # confirmar modelo precargado
docker compose logs agent | grep -o '"transcript_delay": [0-9.]*'
docker compose run --rm client npx ng build       # verificar compilación estricta del cliente
lk token create --join --room <sala> --identity <nombre> --valid-for 24h   # lk es un alias a Docker
```

## Estado

Hecho (pasos 1–16):
- Cuentas: AWS (experiencia simplificada, us-east-2; cuota GPU G/VT de 8 vCPU **aprobada** tras apelación),
  LiveKit Cloud (proyecto `agilina`), ElevenLabs (voz predeterminada, `eleven_v4_turbo`), Gemini.
- HU-01.4 cumplida: el cliente Angular compila en modo estricto y conecta a la sala.
- Agente con cadena STT → LLM/plantilla → TTS funcionando en una sala con un participante.
- Línea base en CPU (Whisper small, precargado): **3,4–3,5 s** desde el fin del habla hasta la transcripción.
- Paso 13: turnos entre dos participantes funcionando (sala `turnos-06`; 3,0–3,5 s fin de voz → transcripción).
  Cliente con botón de micrófono (`publishDefaults.stopMicTrackOnMute`, entra apagado).
  Agente: fin de turno por STT (`turn_detection="stt"`, `min_delay` 1,0 s), ignora turnos de < 3 palabras en
  modo plantilla, espera al primer participante para saludarlo por nombre.
- Pasos 14–16: g4dn.xlarge (Tesla T4, Deep Learning Base AMI Ubuntu 24.04, disco ampliado a 80 GB) con whisper,
  whisper-warmup y agent (`docker-compose.gpu.yml`, speaches `0.8.3-cuda`); el agente usa Whisper por la red interna.
  Fin de voz → transcripción: small 0,95–1,17 s; `deepdml/faster-whisper-large-v3-turbo-ct2` 1,13–1,21 s (cumple U1).
  Recomendación: large-v3-turbo. Con `WHISPER_PROMPT`, "Keycloak" se transcribe bien sin costo de latencia.

Pendiente:
17. Registrar métricas por tramo en CSV (ChatMessage.metrics), grabar la sala, `nvidia-smi` durante las pruebas.
18. Diez interacciones con dos personas reales (Diego y Angélica), una sala nueva por sesión de pruebas.
19. Medir Gemini sobre una transcripción sintética de ~15 min (si se acordó en el Planning).
20. Informe en `docs/spikes/` (main, por PR) contra `UMBRALES.md`; decisión según la regla de decisión.
21. Firma de ambos. 22. Decisiones a flujos y ADR. 23. Terminar la instancia GPU y archivar la rama.

Deuda conocida del prototipo (anotar, no necesariamente resolver):
- Cargar Silero VAD una vez por proceso (hoy bloquea ~160 ms al iniciar cada sesión).
- La rotación de turnos no termina nunca (en la app real, la ceremonia acaba cuando todos hablaron, HU-26).
- Si quien tiene la palabra se desconecta, se cierra la sesión del agente (`close_on_disconnect=True` por defecto).

## Trampas conocidas

- **zsh**: `$m:generateContent` se interpreta como modificador. Usar siempre `${m}` junto a `:`.
- **Compose**: un script para `sh -c` va como un solo argumento (`entrypoint: [sh, -c, |...]`), no en `command` como texto.
- **Salas**: el agente solo se despacha cuando la sala se crea. Si alguien entra antes de que cierre la anterior,
  no llega agente nuevo. Usar un nombre de sala nuevo por sesión (`turnos-03`, `medicion-01`, ...).
- **Gemini**: la cuenta principal de Google está restringida (403 "denied access"). La llave actual es de otra cuenta
  en nivel gratuito: Google puede usar los datos, así que solo frases de prueba inventadas.
  `gemini-3.8-flash` se satura (503/504); respaldo verificado: `gemini-3.5-flash-lite`. `gemini-2.5-flash` no existe para usuarios nuevos.
- **ElevenLabs**: el plan gratuito no permite voces de la Voice Library por API; solo voces predeterminadas.
- **Audio**: usar audífonos; sin ellos, Agilina se transcribe a sí misma. El micrófono solo funciona en localhost o HTTPS.
- **AWS**: el límite de gasto pausa el proyecto según el pronóstico del mes, no el gasto real; al encender la GPU con
  límite de USD 20, AWS detuvo la instancia. Límite temporal USD 400 y `sudo shutdown -h +120` en cada sesión.
- **Instancia GPU**: la IP pública cambia en cada encendido. El disco de 35 GB por defecto no alcanza (usar ≥ 80 GB).
- **.env**: al agregar variables con `echo >> .env`, si el archivo no termina en salto de línea la variable queda
  pegada a la anterior. Verificar con `printenv` dentro del contenedor.

## Cómo trabajamos

- Claude Code edita, compila, levanta servicios y lee logs aquí.
- El chat del proyecto se usa para planear, decidir y revisar resultados. Al volver al chat, se comparte lo nuevo de
  `HALLAZGOS.md` y el estado de este archivo.
- Al cerrar un paso, actualiza la sección **Estado** de este archivo y agrega el hallazgo correspondiente.
