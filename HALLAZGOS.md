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
