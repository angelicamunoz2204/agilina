# Spike HU-01 — Umbrales de éxito

> Fijados el 2 de octubre de 2026, **antes** de ejecutar cualquier medición.
> La fecha del commit de este archivo es la evidencia de que no se ajustaron a los resultados.
> Estado: borrador hasta que ambos desarrolladores lo aprueben.

## Protocolo de medición

- 10 interacciones, 2 participantes humanos, cada uno desde su propio dispositivo.
- Intervenciones de entre 5 y 15 segundos, en español, con frases de daily realistas.
- Misma configuración para las 10: modelo de Whisper, instancia, región y modelo de TTS anotados en el informe.
- "Cumple" significa que al menos 9 de las 10 interacciones están dentro del umbral.

## Umbrales

| # | Qué se mide | Umbral | Origen |
|---|---|---|---|
| U1 | Transcripción: fin del habla → transcripción final (retraso de fin de enunciado + duración del STT) | < 3 s | HU-19, criterio 1 |
| U2 | Síntesis: primer byte de audio de ElevenLabs tras enviar el texto (TTFB) | < 2 s | HU-23, criterio 3 |
| U3 | Latencia conversacional percibida: fin del habla → inicio de la voz de Agilina, medida sobre la grabación de la sala | ≤ 5 s (deseable ≤ 3 s) | Arquitectura §2.2, objetivo inicial 3–5 s |
| U4 | Costo de la instancia GPU por hora (on-demand, us-east-2) | ≤ USD 0,526/h | Propuesta, presupuesto de servicios |
| U5 | Costo de GPU por ceremonia de 15 min, incluido el arranque de la instancia | Se mide y se reporta; sirve de línea base para HU-19 | Arquitectura §2.2, costo operativo |
| U6 | Caracteres de ElevenLabs por ceremonia estimada | Una daily al día cabe en el nivel gratuito | HU-23, criterio 5 |

## Nota sobre el LLM (AD-19)

La cadena del spike incluye Gemini dentro del bucle porque así lo pide el criterio 2 de HU-01.
Sin embargo, por AD-19, Agilina no usa el LLM durante la ceremonia: interviene con plantillas.
Por eso U3 se reporta dos veces:

- **Con LLM:** lo que mide literalmente la cadena del spike.
- **Sin LLM:** fin de enunciado + STT + TTS, que es el camino real de la ceremonia.

La viabilidad se decide sobre el valor **sin LLM**. El valor con LLM se reporta como información.

## Regla de decisión

- **Continuar con la arquitectura** si se cumplen U1, U2, U3 (sin LLM) y U4.
- **Ajustar dentro de la arquitectura** si falla U1 o U3: probar un modelo de Whisper más pequeño o una GPU más potente, y repetir la medición.
- **Revisar el proveedor de GPU** si falla U4 (alimenta la decisión abierta AWS vs. proveedor especializado).
- **Cambiar la arquitectura** solo si U1 o U3 siguen fallando después del ajuste.
