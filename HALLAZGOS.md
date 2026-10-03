
## Paso 11 · Whisper local en CPU (solo desarrollo)
- Servidor: speaches v0.8.2 (API compatible con OpenAI), imagen CPU fijada por digest.
- speaches no descarga modelos solo: hay que pedirlo con POST /v1/models/<id>.
- Modelo: Systran/faster-whisper-small, idioma es.
- Prueba con el audio de ElevenLabs (~4 s): transcripción exacta en las 4 ejecuciones.
- Tiempos en CPU (Mac): 2,44 s la primera vez; luego 2,41, 2,03 y 2,01 s.
  La diferencia en frío es pequeña con este modelo; se vuelve a medir en GPU con un modelo mayor.
