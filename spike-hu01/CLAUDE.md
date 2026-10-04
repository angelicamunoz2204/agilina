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
- Antes de cada commit, `git status` para confirmar que no entra `.env`, audios ni CSV de métricas.

## Estructura

```
spike-hu01/
├── CLAUDE.md, README.md, UMBRALES.md, HALLAZGOS.md
├── docker-compose.yml   # client, agent, whisper, whisper-warmup
├── .env / .env.example
├── client/              # Angular 22 + livekit-client 2.22 (cliente mínimo de sala)
├── agent/               # Python 3.12 + livekit-agents 1.8.4 (agent.py, requirements.txt, Dockerfile)
└── whisper/warmup.wav   # audio corto para precalentar el modelo
```

## Servicios

| Servicio | Qué hace |
|---|---|
| `client` | Cliente Angular en http://localhost:4200. URL y token se pegan en pantalla. |
| `whisper` | speaches v0.8.2 (API compatible con OpenAI) en :8000, imagen CPU fijada por digest. `WHISPER__TTL=-1`. |
| `whisper-warmup` | Espera a Whisper y envía `warmup.wav` para cargar el modelo. speaches no tiene opción de precarga. |
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

Hecho (pasos 1–13):
- Cuentas: AWS (experiencia simplificada, us-east-2, límite USD 20; cuota GPU G/VT de 8 vCPU **solicitada**),
  LiveKit Cloud (proyecto `agilina`), ElevenLabs (voz predeterminada, `eleven_v4_turbo`), Gemini.
- HU-01.4 cumplida: el cliente Angular compila en modo estricto y conecta a la sala.
- Agente con cadena STT → LLM/plantilla → TTS funcionando en una sala con un participante.
- Línea base en CPU (Whisper small, precargado): **3,4–3,5 s** desde el fin del habla hasta la transcripción.
- Paso 13: turnos entre dos participantes funcionando (sala `turnos-06`; 3,0–3,5 s fin de voz → transcripción).
  Cliente con botón de micrófono (`publishDefaults.stopMicTrackOnMute`, entra apagado).
  Agente: fin de turno por STT (`turn_detection="stt"`, `min_delay` 1,0 s), ignora turnos de < 3 palabras en
  modo plantilla, espera al primer participante para saludarlo por nombre.

Pendiente:
14. Lanzar la g4dn.xlarge cuando se apruebe la cuota (Deep Learning AMI, security group solo a nuestras IPs).
15. Whisper en GPU con la imagen CUDA de speaches y un modelo mayor; probar con `curl`; documentar despliegue y costo/hora.
16. Apuntar el agente a la GPU (`WHISPER_BASE_URL=http://<ip>:8000/v1`). Apagar la instancia al terminar cada sesión.
17. Registrar métricas por tramo en CSV (ChatMessage.metrics), grabar la sala, `nvidia-smi` durante las pruebas.
18. Diez interacciones con dos personas reales (Diego y Angélica), una sala nueva por sesión de pruebas.
19. Medir Gemini sobre una transcripción sintética de ~15 min (si se acordó en el Planning).
20. Informe en `docs/spikes/` (main, por PR) contra `UMBRALES.md`; decisión según la regla de decisión.
21. Firma de ambos. 22. Decisiones a flujos y ADR. 23. Terminar la instancia GPU y archivar la rama.

Deuda conocida del prototipo (anotar, no necesariamente resolver):
- Probar `prompt` de vocabulario en Whisper ("Keycloak" se transcribe como "KeyClub").
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

## Cómo trabajamos

- Claude Code edita, compila, levanta servicios y lee logs aquí.
- El chat del proyecto se usa para planear, decidir y revisar resultados. Al volver al chat, se comparte lo nuevo de
  `HALLAZGOS.md` y el estado de este archivo.
- Al cerrar un paso, actualiza la sección **Estado** de este archivo y agrega el hallazgo correspondiente.
