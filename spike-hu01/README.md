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

## Despliegue en GPU

En la instancia (g4dn.xlarge, Tesla T4) corren `whisper`, `whisper-warmup` y `agent`; el cliente sigue en el Mac.
El override `docker-compose.gpu.yml` cambia Whisper a la imagen CUDA, reserva la GPU y no publica el puerto 8000.

1. Encender la instancia en la consola de AWS (us-east-2) y anotar su IP pública: cambia en cada encendido.
2. Subir el proyecto desde el Mac:

   ```bash
   GPU_LLAVE=~/.ssh/<llave>.pem scripts/subir-gpu.sh <ip>
   ```

3. Copiar el `.env` aparte (el script imprime el comando exacto). En la instancia, el `.env` debe tener
   `WHISPER_BASE_URL=http://whisper:8000/v1` y el modelo a medir en `WHISPER_MODEL`:
   `Systran/faster-whisper-small` (referencia) o `deepdml/faster-whisper-large-v3-turbo-ct2`.

   ```bash
   scp -i ~/.ssh/<llave>.pem .env ubuntu@<ip>:spike-hu01/.env
   ```

4. Entrar y verificar Compose (≥ 2.24.4, por `!reset`) y la GPU:

   ```bash
   ssh -i ~/.ssh/<llave>.pem ubuntu@<ip>
   docker compose version
   nvidia-smi
   ```

5. Levantar en la instancia, desde `~/spike-hu01`:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build whisper whisper-warmup agent
   ```

   La primera vez el warmup descarga el modelo (turbo: ~1,6 GB) antes de transcribir; el agente arranca cuando termina.

6. Confirmar la carga del modelo y que el agente quedó registrado:

   ```bash
   docker compose logs whisper | grep -i "loaded in"
   docker compose logs whisper-warmup
   docker compose logs agent | grep "registered worker"
   ```

   Para cambiar de modelo: editar `WHISPER_MODEL` en el `.env` de la instancia y
   `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --force-recreate whisper-warmup agent`.

7. **Al terminar cada sesión, detener la instancia** en la consola de AWS: se cobra por hora mientras esté encendida.
   Los modelos descargados quedan en el volumen `hf-hub-cache` del disco de la instancia.
