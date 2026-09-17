# Contrato entre el worker y la API

El worker solo necesita dos operaciones contra la API. Todo lo demás que ocurre
durante la ceremonia se resuelve dentro del worker o por el canal de datos de
LiveKit.

| Operación | Cuándo | Qué viaja |
| --- | --- | --- |
| `GET /v1/ceremonias/{id}/contexto` | Antes de entrar a la sala | `ContextoCeremonia` |
| `POST /v1/ceremonias/{id}/resultado` | Al cerrar la ceremonia | `ResultadoCeremonia` |

Los tipos viven en `shared/src/agilina_shared/contrato.py` y los importan los
dos desplegables: el contrato es código compartido, no documentación que se
desactualiza. Esta página explica el porqué; la forma exacta está en el tipo.

## Reglas

- **Autenticación.** Credenciales de cliente de la cuenta de servicio del worker
  en Keycloak. El worker nunca usa el token de un usuario.
- **Reintento.** La entrega del resultado reintenta: perder una ceremonia por un
  reinicio de la API no es aceptable. Pedir el contexto no reintenta: si falla,
  la ceremonia no empieza.
- **Campos desconocidos.** Los modelos los rechazan. Una incompatibilidad entre
  versiones falla de inmediato en vez de perder datos en silencio.
- **Tiempos.** Todo en UTC.
- **Sin base de datos.** El worker no toca Postgres: la API es la única fuente
  de verdad del dominio.

## Cambiarlo

Un cambio incompatible es un `BREAKING CHANGE` declarado en el pie del commit y
sube `VERSION_CONTRATO` en `agilina_shared`. Agregar un campo opcional no lo es.

## Qué no cruza por aquí

Los controles de la ceremonia —iniciar la daily, terminar turno, cerrar— viajan
por el canal de datos de LiveKit directo al worker, que valida el permiso
contra el roster con la identidad que aporta el token firmado. No pasan por la
API y por eso no están en este contrato.
