# Spike HU-01 — Hallazgos

> Se registran en el momento, con datos concretos. Son la fuente del informe.
> Los tiempos en CPU son de desarrollo (Mac, Whisper small) y sirven solo como referencia:
> la medición formal se hace en GPU, con el protocolo de `UMBRALES.md`.

## Configuración actual

| Componente | Versión / valor |
|---|---|
| Cliente | Angular 22.2, TypeScript 6.0.2, livekit-client 2.22.3 |
| Agente | Python 3.12, livekit-agents 1.8.4 (plugins 1.8.4), livekit rtc 1.1.20 |
| STT | speaches 0.8.3 (`0.8.3-cpu` fijado por digest; `/openapi.json` dice v0.8.2), Systran/faster-whisper-small, idioma es. GPU: `0.8.3-cuda` |
| TTS | ElevenLabs eleven_v4_turbo, voz predeterminada |
| LLM | gemini-3.5-flash-lite (respaldo; gemini-3.8-flash saturado), cuenta secundaria en nivel gratuito |
| Salas | LiveKit Cloud, proyecto agilina; worker registrado en US East B |
| Nube | AWS, experiencia simplificada, us-east-2, límite de gasto USD 400 temporal (USD 20 al terminar); cuota GPU G/VT de 8 vCPU aprobada; g4dn.xlarge con disco de 80 GB |

## Fase 0 · Cuentas y servicios
- AWS asigna a las cuentas nuevas una experiencia simplificada organizada en proyectos, con límite de gasto
  por proyecto y región fija según el país del contacto (Colombia → us-east-2). La cuota
  "Running On-Demand G and VT instances" arranca en 0: se solicitaron 8 vCPU (g4dn.xlarge usa 4).
- El CLI de LiveKit (`lk`) corre desde Docker con un alias; la sesión persiste en un volumen.
- Google AI Studio solo emite llaves nuevas con prefijo `AQ.` (53 caracteres); ya no `AIza`.
- En el nivel gratuito de Gemini, Google puede usar el contenido enviado para mejorar sus productos:
  en desarrollo solo frases inventadas; transcripciones reales exigen nivel pago.
- ElevenLabs, plan gratuito: las voces de la Voice Library no se pueden usar por API (`paid_plan_required`).
  Se usa una voz predeterminada. Una voz de biblioteca en producción suma el costo del plan de ElevenLabs.
- Modelos de ElevenLabs de baja latencia disponibles: eleven_v4_turbo y eleven_flash_v2_5, ambos a la mitad
  de créditos por carácter. Medir el TTFB de ambos en la fase 4.

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

## Paso 11 · Whisper local en CPU (solo desarrollo)
- Servidor: speaches v0.8.2 (API compatible con OpenAI). La etiqueta de versión de la imagen dice 24.04,
  que es la de Ubuntu; la versión real se lee en `/openapi.json`. Imagen fijada por digest.
- speaches no descarga modelos solo: hay que pedirlo con `POST /v1/models/<id>`.
- Prueba con el audio de ElevenLabs (~4 s): transcripción exacta en las 4 ejecuciones.
  Tiempos: 2,44 s la primera vez; luego 2,41, 2,03 y 2,01 s.
- speaches descarga el modelo de memoria tras 300 s sin uso (TTL por defecto). Se fijó `WHISPER__TTL=-1`.
- `WHISPER__TTL=-1` evita descargar el modelo, pero no lo carga al arrancar el contenedor.
  speaches v0.8.2 **no tiene opción de precarga** (la línea `Config:` no la muestra; `PRELOAD_MODELS` no funciona).
  Solución: contenedor `whisper-warmup` que envía un audio corto al arrancar; el agente depende de que
  termine bien (`service_completed_successfully`). Resultado: modelo cargado en 1,19 s al arrancar.

## Paso 12 · Cadena STT → LLM → TTS

### Acceso a Gemini (bloqueo externo, resuelto)
- `gemini-2.5-flash` ya no está disponible para usuarios nuevos; Google redirige a `gemini-3.8-flash`.
- Cuenta principal de Google: nivel de facturación "No disponible" y 403 "Your project has been denied access"
  en `generateContent`, aunque la misma llave lista los modelos. En septiembre de 2026 hubo muchos reportes
  idénticos en el foro de Google; según Google, indica una marca sobre la cuenta. Configurar facturación
  suele levantarla, pero se pierde el nivel gratuito.
- Nivel pago: solo prepago, mínimo COP 100.000 (elevado "por motivos de seguridad"), no reembolsable,
  solo para Gemini y con vencimiento a un año. Los USD 300 de bienvenida de Google Cloud no cubren Gemini.
  Decisión: no pagar para el spike.
- Con una cuenta de Google distinta, el nivel gratuito sí funciona: la restricción era de la cuenta, no del proyecto.
- Disponibilidad del nivel gratuito: 503 "high demand" en gemini-3.8, 3.7 y 3.6-flash a la vez; se resolvió en
  minutos. En sala, gemini-3.8-flash dio 504 (timeout de ~11 s) y luego 503. Respaldo verificado:
  gemini-3.5-flash-lite y gemini-3.1-flash-lite. Implicación para el resumen de cierre: reintentos con espera
  exponencial, modelo de respaldo y posiblemente nivel pago.
- **Riesgo de proyecto:** los documentos asumían Gemini gratuito; esa suposición ya no es segura.
  Registrar como riesgo y decidir con el director (acceso gratuito, prepago o LLM alternativo).
- El agente quedó con dos modos: `USAR_LLM=1` (Gemini) y `USAR_LLM=0` (respuesta por plantilla,
  coherente con AD-19).

### Latencia (CPU, referencia)
- Primera prueba en sala: 4,36 s desde el fin del habla.
  Desglose: ~0,8 s espera del VAD + 1,05 s carga en frío del modelo + ~2,5 s transcripción (6,1 s de audio).
- Segunda: 4,20 s (incluye carga en frío de 1,11 s; faltaba `WHISPER__TTL`).
- Tercera: 5,60 s = ~0,8 s VAD + 2,38 s carga del modelo (primera petición tras recrear el contenedor)
  + 2,42 s transcripción (6,4 s de audio). Origen del contenedor de precalentamiento.
- Con el modelo precargado: 3,53 s y 3,41 s. **Línea base en CPU (small): 3,4–3,5 s**, por encima de U1 (< 3 s).
- Respuesta con LLM registrada ~8,1 s después de cerrar el turno (incluye Gemini, síntesis y reproducción;
  la medición por tramo es de la fase 4).

### Calidad de transcripción y resumen
- "Keycloak" → "KeyClub" (dos veces) y "kicklock"; "Hoy sigo" → "voy seguro"; "agente" → "de la gente".
  Errores en términos técnicos y también en palabras comunes: comparar con el modelo grande en GPU
  y probar el `prompt` de vocabulario de Whisper (insumo para HU-24).
- Gemini repitió "KeyClub" en el resumen: los errores del STT se propagan al LLM sin corrección.
- Gemini agregó contenido inexistente ("con datos reales"). Para el resumen de cierre: instrucciones estrictas
  de fidelidad y validación contra la transcripción.
- Con "endpoint" y "API" la transcripción fue exacta y el resumen fiel.

### Comportamiento de LiveKit
- LiveKit Cloud activa por defecto un detector de fin de turno y otro de interrupciones en su gateway:
  parte del audio sale a un tercero más (privacidad) e influye en cuánto espera Agilina para responder.
  En una sesión el detector en la nube no respondió en 1 s y el agente usó un modelo local de respaldo.
- El primer trabajo tras reiniciar el worker puede esperar ~1–2 s a que se cree un proceso ("no warmed process").
- Cargar Silero VAD en el entrypoint bloquea el agente ~160 ms al iniciar cada sesión;
  en producción conviene cargarlo una vez por proceso.
- `python agent.py dev` está deprecado (LiveKit recomienda `lk agent dev`); usar `start` en el contenedor.
- Si alguien entra a la sala antes de que LiveKit cierre la anterior, no se despacha un agente nuevo.
  Protocolo de medición: una sala nueva por sesión de pruebas.

## Paso 13 · Turnos entre participantes (cumplido)
- El agente cambia la pista que escucha con `session.room_io.set_participant` y anuncia
  "<nombre>, tienes la palabra" al terminar su respuesta. Es el modelo de turnos de HU-26.
- Con dos ventanas del navegador en el mismo Mac, el agente no recibe voz: Whisper recibió una sola petición
  de 1,4 s en 35 s y no hubo transcripciones. Hipótesis: ambas ventanas capturan el mismo micrófono.
  Siguiente prueba: botón de micrófono con `stopMicTrackOnMute: true`.
- En livekit-client 2.22.3, `stopMicTrackOnMute` no es opción directa de `Room`: va en
  `publishDefaults` (`new Room({ publishDefaults: { stopMicTrackOnMute: true } })`); el build estricto lo detectó.
  El cliente ahora entra con el micrófono apagado y lo alterna con un botón (signal `micActivo`).
- El protocolo de `UMBRALES.md` exige un dispositivo por participante: las dos ventanas solo sirven
  para desarrollo.
- El saludo puede decir "equipo" en vez del nombre si el participante aún no está vinculado al arrancar.
- El botón de micrófono (stopMicTrackOnMute) resolvió la falta de voz: confirmado el problema de micrófono compartido.
- En CPU la transcripción (~2,5 s) tarda más que la espera de fin de turno (0,3 s): el VAD cierra el turno antes
  de que llegue el texto. La frase llegó cuando el turno ya era de otro participante, abrió un turno nuevo,
  interrumpió el anuncio "andres, tienes la palabra" y la palabra volvió a Diego.
  Implicación para HU-20: la atribución debe basarse en la pista de origen del audio, no en el participante
  vinculado en el momento en que llega el texto.
- Whisper transcribió 1,3 s de audio inicial como "Gracias." (posible alucinación con ruido al activar el micrófono).
- livekit-agents 1.8.4: `min_endpointing_delay` y `max_endpointing_delay` de `AgentSession` están deprecados;
  lo vigente es `turn_handling={"endpointing": {"min_delay", "max_delay", "mode"}}`. Hay dos juegos de valores por
  defecto en `turn.py`: 0,5/3,0 s en general y **0,3/2,5 s cuando hay detector de turno en streaming**, que es el
  caso de LiveKit Cloud (`turn-detector-v1`); por eso los logs muestran `endpointing_delay: 0.3`.
  `max_delay` se usa cuando el detector considera improbable que el participante haya terminado: debe ser ≥ `min_delay`.
- La espera se cuenta desde el último instante con voz según el VAD (`last_speaking_time`), y con speaches
  (STT sin streaming) la petición a Whisper solo sale cuando el VAD da por terminada la voz.
  Cronología de la sala `turnos-01` (UTC):
  03:37:17,8 se abre el micrófono de diego · 03:37:20,1 Whisper recibe 1,3 s → "Gracias." (logprob −1,06)
  · 03:37:27,11 fin de la voz · 03:37:27,69 turno cerrado por VAD (EOU 0,74, `from_cache: true`) con solo "Gracias."
  · 03:37:27,79 Whisper recibe 7,7 s · 03:37:29,97 responde "Gracias, quedó anotado." y vincula a andres
  · 03:37:30,25 llega la transcripción real (**3,14 s después del fin de la voz**; 2,45 s de Whisper)
  · aviso "transcript arrives after turn has been committed" · abre un turno nuevo (`source: stt`), interrumpe
  "andres, tienes la palabra" (mensajes de ElevenLabs "for inactive context") y la palabra vuelve a diego.
- Implicación: con `min_delay` = 3,0 s, esa misma frase se habría cerrado 0,14 s antes de que llegara el texto.
  El tiempo de Whisper crece con la duración del audio (2,45 s para 7,7 s), y el protocolo admite intervenciones
  de hasta 15 s: en CPU un retraso fijo tendría que ser de ~5 s o más.
- Decisión: fin de turno por STT (`turn_handling={"turn_detection": "stt", "endpointing": {"min_delay": 1.0}}`)
  en lugar de un retraso fijo. En 1.8.4, si no hay transcripción todavía, el agente no evalúa el fin de turno
  (`audio_recognition.py`, "stt enabled but no transcript yet"): el turno se cierra cuando llega el texto, o al
  cumplirse 1 s desde el fin de la voz si el texto llega antes. Se adapta solo a lo que tarde Whisper (CPU o GPU)
  y deja de enviar audio al detector de turno de LiveKit Cloud (el de interrupciones sigue activo).
- Hueco conocido: el adaptador de STT sin streaming (`StreamAdapter`) emite `END_OF_SPEECH` al terminar cada
  segmento del VAD, antes de llamar a Whisper. Si un turno tiene dos segmentos (pausa > ~0,55 s) y el primero ya
  tiene texto, el turno se cierra con ese texto 1 s después del fin de la voz, sin esperar el segundo. Si el primer
  fragmento es ruido corto ("Gracias."), el filtro de menos de 3 palabras lo descarta y el segundo llega como turno
  propio; si es habla real, Agilina responde a mitad de la intervención. Solución robusta (insumo para HU-26):
  cierre manual del turno (`turn_detection="manual"` + `commit_user_turn()`) cuando no quede STT pendiente.
- Otros ajustes: en modo plantilla, los turnos de menos de 3 palabras se ignoran sin responder ni ceder el turno;
  el agente espera al primer participante (`ctx.wait_for_participant()`) y arranca la sesión vinculada a él
  (`RoomOptions(participant_identity=...)`), así el saludo ya no dice "equipo".
- Efecto en la medición: U1 no cambia (fin de la voz → transcripción); U3 suma `min_delay` solo cuando Whisper
  responde en menos de 1 s. Reportar la configuración de fin de turno junto a U3.
- Decisión: el turno lo cierra el participante con un botón de "terminar turno" (cierre manual,
  turn_detection="manual" + commit_user_turn()). El cierre debe esperar a que no queden
  transcripciones pendientes. Por eso no se evalúa el partido de turnos por pausas del VAD.
  Para la medición: registrar también el tiempo del clic a la última transcripción.

### Prueba en sala `turnos-06` (dos ventanas, `USAR_LLM=0`, fin de turno por STT)
- Funcionó: saludo con nombre ("diego, tienes la palabra"), tres turnos completos alternando diego → andres → diego,
  cada uno cerrado justo al llegar la transcripción (`source: stt`), sin avisos de transcripción tardía
  ni anuncios interrumpidos. No hubo "Gracias." alucinado: el filtro de menos de 3 palabras no se ejercitó.
- Tiempos (CPU, small), fin de la voz → transcripción (`transcript_delay`): **3,45 s, 3,30 s y 3,02 s**.
  Desglose: ~0,65–0,75 s hasta que el VAD da por terminada la voz y sale la petición + Whisper 2,69 s (6,1 s de audio),
  2,64 s (7,1 s) y 2,35 s (6,1 s). Coincide con la línea base (3,4–3,5 s), por encima de U1 (< 3 s).
- La rotación no termina: el agente alterna indefinidamente porque no sabe cuándo ya hablaron todos.
  En la app real la ceremonia termina cuando cada participante tuvo su turno (HU-26).
- Al salir andres (que tenía la palabra), LiveKit cerró toda la sesión del agente: "closing agent session due to
  participant disconnect". Por defecto `close_on_disconnect=True` en `RoomOptions`. En la app real hay que
  desactivarlo y pasar el turno al siguiente si quien habla se desconecta.
- Aviso "stt end of speech received while vad is still in a speech segment, flushing vad": el adaptador de STT tiene
  su propio VAD y terminó antes que el de la sesión; sin efecto visible.
- Errores de transcripción: "instancia" → "distancia", "API" → "IPI", "Keycloak" → "KeyClub" (otra vez),
  "mediodía" sin tilde. Insumo para comparar con el modelo grande y el `prompt` de vocabulario.

## Ajuste · Agente en modo `start`
- El Dockerfile pasó de `python agent.py dev` (deprecado) a `python agent.py start --log-level debug`.
  `start` registra en INFO por defecto: sin `--log-level debug` se pierden `transcript_delay` y "user turn committed",
  que se usan para medir. También acepta la variable `LIVEKIT_LOG_LEVEL`.
- En `start` los logs salen en JSON (una línea por evento, sin colores); el `grep` de `transcript_delay` sigue sirviendo.
- `start` precalienta procesos al arrancar (4 inicializados en el Mac). En `dev` el primer trabajo esperaba
  ~1,4–1,5 s a que se creara un proceso ("no warmed process available"); verificar en la próxima sala.

## Paso 14 · Instancia GPU
- g4dn.xlarge en us-east-2: USD 0,526/h (Linux, on-demand), exactamente en el límite de U4 (≤ 0,526). Cumple sin margen.
- AMI: Deep Learning Base AMI with Single CUDA (Ubuntu 24.04, x86). Trae driver NVIDIA 595.91, CUDA 13.2,
  Docker y NVIDIA Container Toolkit: `docker run --gpus all` ve la GPU sin instalar nada.
- GPU: Tesla T4, 15 GB de memoria.
- Security group solo con SSH desde la IP de Diego; ningún puerto de servicio expuesto.
- La apelación funcionó: AWS aprobó 8 vCPU G/VT en us-east-2 tras reducir el pedido a una instancia
  y detallar el caso de uso. Para cuentas nuevas: la cuota de GPU no es inmediata; hay que pedirla
  con justificación y prever días de espera en la planificación.

## Paso 15 · Despliegue de Whisper en GPU (desplegado y medido)
- Versión real de la imagen de CPU: el digest fijado (`21e3df06…`) es el índice de **`0.8.3-cpu`**
  (era `latest-cpu` al fijarlo), aunque `/openapi.json` reporta `v0.8.2`. La versión de speaches del spike es 0.8.3.
- Imagen GPU: `0.8.3-cuda`, fijada por el digest del índice `9abc6968…` (amd64 `f3438861…`).
  Variantes de 0.8.3: `cuda` = CUDA 12.9 (driver ≥ 575), `cuda-12.6.3` y `cuda-12.4.1`. Con el driver 595.91 de la AMI
  sirve la estándar. `latest-cuda` no coincide con `0.8.3-cuda`: no usar etiquetas `latest`.
- La imagen CUDA usa el mismo usuario (`ubuntu`) y caché (`/home/ubuntu/.cache/huggingface/hub`): el volumen sirve igual.
- `docker-compose.gpu.yml` (override): imagen CUDA, reserva de GPU (`driver: nvidia`, `count: 1`),
  `WHISPER__COMPUTE_TYPE=float16`, `WHISPER__INFERENCE_DEVICE=cuda` (con `auto` caería a CPU sin avisar si la GPU
  no fuera visible) y `ports: !reset []` (el agente usa la red interna; Compose ≥ 2.24.4). En el Mac hay Compose 2.29.7.
- whisper-warmup ahora hace `POST /v1/models/${WHISPER_MODEL}` antes de transcribir: speaches no descarga modelos solo.
  Si el modelo ya está, responde 200 ("Model '…' downloaded"): probado en CPU, el warmup terminó con código 0.
  En la instancia nueva el POST bloquea mientras descarga (turbo: `model.bin` de 1,6 GB).
- Modelos a comparar (IDs verificados en `GET /v1/registry?task=automatic-speech-recognition` de speaches):
  `Systran/faster-whisper-small` (referencia) y **`deepdml/faster-whisper-large-v3-turbo-ct2`** (multilingüe con es,
  etiqueta `ctranslate2`, ~140 mil descargas, revisión `4df90f75`). El registro de speaches es una búsqueda en
  Hugging Face (611 resultados): hay muchas copias y variantes (int8, ajustes por idioma); no usarlas.
- `scripts/subir-gpu.sh <ip>`: rsync sin `client/`, `node_modules`, `.angular`, `dist`, `metrics/`, `recordings/` ni
  `.env`. Simulado en local: se copian solo agent, whisper, scripts, los compose y los .md.
  `docker compose -f docker-compose.yml -f docker-compose.gpu.yml config` valida sin `client/` (exit 0).
- El límite de gasto de la experiencia simplificada pausa el proyecto según el PRONÓSTICO del mes,
  no el gasto real: con USD 0,48 gastados, encender la g4dn.xlarge proyectó USD 344 (uso continuo)
  y AWS pausó el proyecto (detiene la instancia y una SCP bloquea ec2:StartInstances).
  Con límite de USD 20 la GPU no se puede usar. Solución en el spike: límite temporal de USD 400
  y apagado automático con `shutdown -h +120` en cada sesión.
  Implicación para producción: este control de costos no sirve para GPU de uso intermitente;
  se necesita apagado automático de la instancia y alertas propias.
- GPU con small (sala gpu-01): fin de voz → transcripción en 1,17 / 0,95 / 1,00 s (CPU: 3,0–3,5 s).
  Cumple U1 (< 3 s) con margen. ~0,65–0,75 s es espera del VAD; Whisper en sí, ~0,3–0,4 s.
- El disco raíz por defecto de la Deep Learning Base AMI (35 GB) se llena con la imagen CUDA de speaches,
  las imágenes del agente y los modelos: la descarga de large-v3-turbo falló con "no space left on device"
  (speaches respondió 500). Se amplió el volumen a 80 GB. Recomendación: lanzar con ≥ 80 GB.
  La g4dn.xlarge trae además 116 GB de almacenamiento local (/opt/dlami/nvme) que se borra al detenerla.
- GPU con large-v3-turbo (deepdml/faster-whisper-large-v3-turbo-ct2, sala gpu-02): 1,21 / 1,13 s
  (small: 0,95–1,17 s). Cumple U1 con margen; ~0,1–0,2 s más que small.
- Calidad: "Ayer desplegué el servicio de Whisper en la instancia de prueba. Hoy mido la latencia con
  el modelo grande." transcrita exacta (en CPU con small: "distancia", "de la gente").
  "Keycloak" → "Kiklook": los nombres propios no se resuelven con un modelo mayor; requieren prompt
  de vocabulario.
- Memoria de GPU: small 822 MiB; con turbo cargado, 2.883 MiB en total (los dos modelos residentes
  por WHISPER__TTL=-1). En producción, un solo modelo fijo.
- Recomendación: large-v3-turbo como modelo de Agilina.
- Prompt de vocabulario (WHISPER_PROMPT, sala gpu-04, large-v3-turbo): "Keycloak" transcrito correctamente
  (sin prompt: "Kiklook"). Ambas frases exactas. Latencia 1,15 / 1,12 s: el prompt no añade costo medible.
  Implicación: el vocabulario del equipo (herramientas, nombres propios) debe ser configurable por equipo (insumo para HU-24).
- Trampa: al agregar variables con `echo >> .env`, si el archivo no termina en salto de línea la variable queda
  pegada a la anterior y el agente no la recibe. Verificar con `printenv` dentro del contenedor.
- U2 (TTFB ElevenLabs, eleven_v4_turbo, endpoint /stream, medido desde Colombia): 0,58 / 0,47 / 0,51 s. Cumple (< 2 s).
- U3 estimado (no medido): U1 GPU ~1,1–1,2 s + TTFB ~0,5 s + red ≈ 1,8–2 s sin LLM. Cumple incluso el deseable (≤ 3 s).

## Ajuste · Prompt de vocabulario para Whisper
- livekit-plugins-openai 1.8.4: el parámetro de `openai.STT` es `prompt` (`NotGivenOr[str]`). En la transcripción sin
  streaming se envía como campo `prompt` de `/audio/transcriptions`, y si está vacío lo omite
  (`prompt=transcription.prompt or openai.omit`). También existe `keywords`, pensado para los modelos de OpenAI; no se usa.
- speaches 0.8.3 recibe `prompt` como campo del formulario y lo pasa a faster-whisper como `initial_prompt`
  (`routers/stt.py`).
- El agente lee `WHISPER_PROMPT` (opcional, vacío por defecto = sin prompt). Medido en la sala gpu-04 (ver paso 15):
  "Keycloak" correcto con prompt, sin costo de latencia medible.

## Paso 17 · Instrumentación de métricas por turno (preparada, sin prueba en sala)
- El agente escribe una fila por turno de usuario en `metrics/<sala>.csv` (`agent/metricas.py`; volumen
  `./metrics:/metrics`). Columnas: contexto (sala, participante, hora UTC, `ENTORNO`, modelos, prompt, `USAR_LLM`),
  duración de la voz y del audio enviado al STT, U1 con su desglose, TTFB del LLM, U2, U3 aproximado,
  caracteres a ElevenLabs (respuesta + anuncio) y los textos. `scripts/resumen-metricas.py` resume contra
  `UMBRALES.md` (mediana, máximo, cuántas cumplen; "cumple" = 90 %, U3 separado por `USAR_LLM`).
- Métricas oficiales de livekit-agents 1.8.4 (verificadas en el código instalado):
  - `ChatMessage.metrics` del usuario: `transcription_delay` = llegada de la transcripción final − fin de la voz
    según el VAD (`stopped_speaking_at`). Es U1. Ya viene lleno dentro de `on_user_turn_completed`.
  - `ChatMessage.metrics` de la respuesta: `tts_node_ttfb` (U2), `llm_node_ttft`, `started_speaking_at`
    (primer cuadro de audio entregado a la pista de la sala) y `e2e_latency` = `started_speaking_at` − `stopped_speaking_at`
    del usuario.
  - **`e2e_latency` no se llena en modo plantilla:** `session.say()` solo recibe las métricas del usuario dentro de
    `on_enter`. El agente calcula U3 aproximado con la misma fórmula.
  - Con `StopResponse` el mensaje del usuario no se agrega a la conversación (no hay `conversation_item_added`).
  - `metrics_collected` está deprecado en la sesión ("use session_usage_updated ... y ChatMessage.metrics"), pero no en
    los componentes: el agente escucha `STTMetrics.duration` (petición a Whisper), `STTMetrics.audio_duration` y
    `TTSMetrics.characters_count` (= `len(texto)`) directamente en los objetos STT y TTS.
- Tramos calculados: espera del VAD = U1 − duración de la última petición a Whisper del turno.
  Validado con eventos simulados (fila correcta, saludo fuera del turno, turnos descartados sin fila);
  pendiente la prueba en sala `metricas-01` con 3 intervenciones.
- **Lo que U3 no ve.** `started_speaking_at` es cuando el agente entrega el primer cuadro a su pista (LiveKit
  documenta `playback_latency` ≈ 0 para la salida de sala, sin la entrega por red). Quedan fuera:
  (1) de subida, el tramo micrófono → SFU → agente (el agente fecha el fin de la voz cuando le llega el audio);
  (2) de bajada, agente → SFU de LiveKit Cloud (US East) → navegador en Colombia;
  (3) el búfer de jitter del navegador y la salida de audio del equipo.
  Validación propuesta en 2 o 3 muestras: grabar en el equipo del participante el micrófono y el audio del sistema
  en una misma pista (QuickTime u OBS con un dispositivo de captura del sistema), medir en la forma de onda el
  tiempo entre el fin de la voz y el inicio de la voz de Agilina, y compararlo con `u3_aprox_s` de la misma fila.
  La diferencia es la parte de red y búfer que el agente no ve.

## Cierre · Estimaciones de costo (U5, U6)
- U5 (estimado): ~20 min de instancia por ceremonia (15 de daily + ~5 de arranque) × USD 0,526/h ≈ USD 0,18
  (20/60 × 0,526 = 0,175).
- U6 (estimado): ~45 caracteres por participante (respuesta + anuncio de turno) + ~45 del saludo ≈ 315 por daily
  de 6 personas (6 × 45 + 45). eleven_v4_turbo cobra 0,5 créditos por carácter: ~160 créditos por daily
  (315 × 0,5 = 157,5). El cupo mensual del plan gratuito queda por confirmar en la cuenta.

## Pendientes para el informe
- Criterio 2 de HU-01 (LLM en el bucle): validado en CPU con gemini-3.5-flash-lite; reportar U3 con y sin LLM.
- TTFB de eleven_v4_turbo frente a eleven_flash_v2_5.
- Whisper small frente a un modelo mayor en GPU, con el mismo guion de frases (primera medición: gpu-01 y gpu-02; repetir con el protocolo).
- Efecto del `prompt` de vocabulario en términos técnicos (primera medición: gpu-04; repetir con el protocolo).
- U6: caracteres de ElevenLabs por ceremonia estimada.
