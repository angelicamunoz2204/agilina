# AD-30: todo error HTTP tiene un solo formato, y la API tiene un catálogo escrito

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-07
- **Deciden:** Diego, Angélica
- **Historia:** ninguna; arquitectura (Sprint-0)

## Contexto

La API contestaba sus fallos de tres maneras: el formato propio (`{code, detail, reasons}`), el
de FastAPI (`{"detail": ...}`, con la lista de errores de validación) y un texto plano en los
`500`. Quien consume la API tenía que reconocer tres formas, y la validación devolvía además el
valor enviado (`input`): una contraseña rechazada volvía en la respuesta. Tampoco había manera de
relacionar un error que ve una persona con la línea del registro que lo causó, ni un lugar donde
leer qué puede contestar cada endpoint.

## Decisión

- **Un solo cuerpo** para todo error, venga de una regla de negocio, de la validación, de una
  ruta inexistente o de un fallo inesperado:
  `{"error": {"status", "code", "message", "details"?, "request_id"}}`. El `status` va también
  en el cuerpo; el `message` está en inglés y es genérico (nunca nombra personas, invitaciones ni
  tenants); la web decide y traduce por `code`.
- **Un catálogo de errores en código** (`ApiError(status, code, message, headers)`), por
  contexto (`SharedErrors`, `IdentityErrors`, `TeamsErrors`). Un `code` es único en todo el
  catálogo y no se renombra: es parte del contrato. Una tabla por contexto empareja cada excepción
  de dominio con su entrada; lo que la presentación decide por sí misma lo lanza como
  `ApiException`.
- **Cuatro manejadores** (excepción mapeada, `ApiException`, validación y ruta inexistente, y el
  resto) y un **middleware de `request_id`**: cada respuesta lleva `X-Request-ID` y cada línea del
  registro, el mismo identificador. Un fallo inesperado devuelve `500 internal_error` con el
  `request_id`; su detalle queda solo en el registro.
- **La validación dice dónde y por qué, nunca el valor** (`details.fields[]: {field, reason}`).
- **Cada endpoint declara sus respuestas** con `errors_of(...)`, y `docs/api.md` las lista todas.
  Una prueba falla si una ruta no está en el archivo, si una de sus respuestas no coincide o si un
  código no está en el catálogo. Un endpoint nuevo se documenta en el mismo cambio.
- **Excepción:** `GET /health/ready` devuelve `503` con el cuerpo de la sonda, no con el de error:
  lo lee el orquestador, no una persona.

## Alternativas descartadas

- **Seguir con `{code, detail, reasons}` y adaptar los demás.** No cubre el `status` ni el
  `request_id`, y deja a la validación fuera de forma.
- **RFC 9457 (`application/problem+json`).** Es el estándar, pero exige `type` como URI y el
  cliente de este proyecto es uno solo, la web: un envoltorio propio y más pequeño basta.
- **Mensajes traducidos en la API.** El idioma es del cliente; la API entrega un código estable.

## Consecuencias

- El cliente lee un solo lugar (`error.code`, `error.details`) y la web tiene un único lector
  (`readApiError`).
- Un `code` nuevo es una entrada de catálogo; cambiar o quitar uno es un cambio de contrato.
- El `request_id` permite pedir «el identificador del error» y buscar su traza.
- Una respuesta nueva de un endpoint exige tocar `docs/api.md`; es un costo deliberado.

## Cómo se verifica

- `tests/api/unit/shared/presentation/http/`: el catálogo (códigos únicos, estado de error,
  mensaje), los manejadores (todos los fallos con la misma forma, sin el valor enviado, un `500`
  que no filtra nada) y el middleware (identificador propio, ajeno o inválido; presente en el
  registro).
- `tests/api/unit/bootstrap/test_api_catalog.py`: rutas, estados y códigos de `docs/api.md`
  contra la especificación OpenAPI y el catálogo.
