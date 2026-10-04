# Spike HU-01 — Cadena de voz extremo a extremo

> ⚠️ Prototipo NO productivo. Esta rama nunca se fusiona a main.
> El informe del spike vive en main, en `docs/spikes/`.

Valida que Agilina puede escuchar a los participantes de una sala de LiveKit, transcribir con Whisper,
(opcionalmente) razonar con Gemini y responder con voz de ElevenLabs, y mide la latencia y el costo de esa cadena.

| Archivo | Para qué |
|---|---|
| `UMBRALES.md` | Criterios de éxito, fijados antes de medir. No se modifican. |
| `HALLAZGOS.md` | Registro de todo lo encontrado durante el spike. |
| `CLAUDE.md` | Contexto y reglas para trabajar con Claude Code. |

## Requisitos

- Docker Desktop y Git. Nada más se instala en la máquina.
- Audífonos para las pruebas en sala.

## Levantar todo (agente incluido)

```bash
cp .env.example .env      # y llenar los valores (pedirlos a Diego; no se comparten por el repo)
docker compose up -d --build
docker compose logs whisper | grep -i "loaded in"   # el modelo debe quedar precargado
```

Abrir http://localhost:4200, pegar la URL del proyecto de LiveKit y un token, y entrar a la sala.

## Solo como participante (por ejemplo, Angélica en la prueba con dos personas)

No hace falta el agente ni el `.env`: el agente corre en la máquina de Diego y entra solo a la sala.

```bash
docker compose up -d --build client
```

Abrir http://localhost:4200 y pegar la URL y el token que envía Diego. El micrófono solo funciona en `localhost`.

## Generar tokens

`lk` es el CLI de LiveKit corriendo en Docker:

```bash
alias lk='docker run --rm -it -v ~/.livekit:/root/.livekit livekit/livekit-cli'
lk token create --join --room <sala> --identity <nombre> --valid-for 24h
```

Usar una sala nueva en cada sesión de pruebas: el agente solo entra cuando la sala se crea.
El `identity` es el nombre que Agilina pronuncia al dar la palabra.

## Modos del agente

- `USAR_LLM=0`: responde con una plantilla fija, como en la ceremonia real (AD-19).
- `USAR_LLM=1`: responde Gemini con un resumen de una frase.

Tras cambiar `.env`: `docker compose up -d --force-recreate agent`.
