# Catálogo de la API

Cada endpoint de la API con **todas** sus respuestas posibles. Es la referencia para quien
consume la API (la web, el worker) y para quien revisa un cambio. La especificación completa
y ejecutable está en `/docs` (OpenAPI); este archivo es el resumen que se lee de corrido.

> **Se mantiene junto al código.** Un endpoint nuevo, o una respuesta nueva de uno existente,
> se documenta aquí en el mismo cambio. Una prueba (`tests/api/unit/test_api_catalog.py`) falla
> si una ruta no está aquí, si una ruta de aquí ya no existe, o si un código de error no está en
> el catálogo.

## Convenciones

### Cabeceras

| Cabecera | Sentido | Dónde |
| --- | --- | --- |
| `X-Agilina-Tenant` | La organización a la que se refiere la petición ([AD-29](adr/0029-un-tenant-es-una-organizacion-con-su-base-y-su-realm.md)) | Toda ruta salvo `/health*`, las de ceremonias y la documentación |
| `Authorization: Bearer <token>` | Token de acceso del tenant (Keycloak) | Las rutas «con sesión» |
| `X-Request-ID` | Identificador de la petición. Se acepta el que envíe el cliente si tiene de 8 a 64 caracteres `A-Za-z0-9._-`; si no, la API genera uno. Siempre vuelve en la respuesta | Todas |

### El formato de un error

Todo error HTTP tiene **el mismo cuerpo**, venga de donde venga (regla de negocio, validación,
ruta inexistente o fallo inesperado):

```json
{
  "error": {
    "status": 422,
    "code": "validation_error",
    "message": "The request is not valid.",
    "details": { "fields": [{ "field": "body.password", "reason": "string_too_long" }] },
    "request_id": "c1b9f0a2e47d4c1f"
  }
}
```

| Campo | Qué es |
| --- | --- |
| `status` | El mismo número de la respuesta HTTP |
| `code` | Estable: el cliente decide por él, y la web lo traduce al idioma de la persona |
| `message` | En inglés, para desarrolladores; genérico: nunca nombra personas, invitaciones ni tenants |
| `details` | Solo cuando el código lo define (abajo). **Nunca** repite un valor enviado |
| `request_id` | El de la cabecera `X-Request-ID`; se pide al reportar un problema y aparece en el registro |

Toda respuesta de error lleva `Cache-Control: no-store`.

### Errores que puede dar cualquier endpoint

| Estado | `code` | Cuándo |
| --- | --- | --- |
| 404 | `not_found` | La ruta no existe |
| 405 | `method_not_allowed` | La ruta existe pero no con ese método |
| 500 | `internal_error` | Un fallo inesperado; el detalle queda en el registro bajo el `request_id`, nunca en la respuesta |

### Catálogo de códigos

| Estado | `code` | Significado | `details` |
| --- | --- | --- | --- |
| 400 | `tenant_required` | La petición no trae `X-Agilina-Tenant` | — |
| 404 | `tenant_not_found` | El tenant no existe, está suspendido o el nombre no es válido (la misma respuesta para los tres) | — |
| 401 | `not_authenticated` | Falta el token, o no identifica a un usuario. Lleva `WWW-Authenticate: Bearer` | — |
| 403 | `not_a_team_member` | El usuario no es miembro activo del equipo (ajeno, retirado o inexistente: la misma respuesta) | — |
| 422 | `validation_error` | El cuerpo, un parámetro o una cabecera no es válido | `fields[]`: `{field, reason}` |
| 404 | `invitation_not_found` | El enlace se alteró o nunca existió | — |
| 410 | `invitation_used` | La invitación ya se usó | — |
| 410 | `invitation_expired` | La invitación venció | — |
| 410 | `invitation_revoked` | La invitación se revocó | — |
| 409 | `account_already_exists` | Ese correo ya tiene cuenta | — |
| 409 | `invitation_still_valid` | El enlace aún sirve; no hace falta pedir otro | — |
| 409 | `no_admins_to_notify` | El equipo no tiene a quién avisar | — |
| 422 | `password_policy` | La contraseña incumple la política | `reasons[]`: códigos estables |
| 422 | `password_mismatch` | La contraseña y su confirmación difieren | — |
| 503 | `identity_provider_unavailable` | El proveedor de identidad no responde | — |
| 502 | `mail_unavailable` | No se pudo enviar el correo | — |
| 422 | `invalid_team_name` | El nombre del equipo está en blanco o es demasiado largo una vez recortado | — |
| 404 | `team_not_found` | El equipo no existe | — |
| 501 | `not_implemented` | La operación está definida pero aún no se implementa | — |

## Salud

### `GET /health`

Sonda de vida. Sin tenant, sin sesión.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `{version, environment, status: "alive"}` | Siempre que el proceso responde |

### `GET /health/ready`

Sonda de disponibilidad: comprueba la base del catálogo. Sin tenant, sin sesión.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `{version, environment, status: "ready", database: "up"}` | La base responde |
| 503 | `{version, environment, status: "not_ready", database: "down"}` | La base no responde. **No** usa el formato de error: es el cuerpo de la sonda, que lee el orquestador |

## Tenant

### `GET /v1/tenant`

Los datos públicos del tenant que nombra la petición. La web lo pregunta antes de iniciar sesión.
Requiere tenant; sin sesión.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `{slug, display_name, language}` | El tenant existe y está activo |
| 400 | error `tenant_required` | Falta la cabecera |
| 404 | error `tenant_not_found` | No existe, está suspendido o el nombre no es válido |
| 422 | error `validation_error` | La especificación la declara porque la cabecera es un parámetro, pero es opcional: en la práctica no ocurre |

## Invitaciones

Públicas: la persona aún no tiene cuenta y el token del cuerpo la autoriza. Requieren tenant. Nada
se guarda en caché. El token viaja en el cuerpo, nunca en la URL.

### `POST /v1/invitations/status`

Qué muestra la página de activación sobre un enlace. Cuerpo: `{token}`.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `{email, full_name, role, status, expires_at}` | La invitación está pendiente |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 404 | error `invitation_not_found` | El enlace se alteró o nunca existió |
| 410 | error `invitation_used` / `invitation_expired` / `invitation_revoked` | La invitación ya no sirve |
| 422 | error `validation_error` | Cuerpo mal formado |

### `POST /v1/invitations/activate`

Elige una contraseña y activa la cuenta. Cuerpo: `{token, password, confirmation}`.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 201 | `{email, team_id, role}` | La cuenta quedó activa |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 404 | error `invitation_not_found` | El enlace se alteró o nunca existió |
| 409 | error `account_already_exists` | Ese correo ya tiene cuenta |
| 410 | error `invitation_used` / `invitation_expired` / `invitation_revoked` | La invitación ya no sirve |
| 422 | error `validation_error` | Cuerpo mal formado (falta un campo, contraseña de más de 256 caracteres…) |
| 422 | error `password_mismatch` | `password` y `confirmation` difieren |
| 422 | error `password_policy` | La política la rechaza; `details.reasons` dice por qué. El enlace sigue vigente |
| 503 | error `identity_provider_unavailable` | Keycloak no responde |

### `POST /v1/invitations/request-new`

Pide a los admins del equipo una invitación nueva. Cuerpo: `{token}`.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 202 | `{status: "requested"}` | Se avisó a los admins |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 404 | error `invitation_not_found` | El enlace se alteró o nunca existió |
| 409 | error `invitation_still_valid` | El enlace aún sirve |
| 409 | error `no_admins_to_notify` | Nadie a quien avisar |
| 422 | error `validation_error` | Cuerpo mal formado |
| 502 | error `mail_unavailable` | No se pudo enviar el correo |

## Equipos

Todas requieren tenant y sesión: el usuario es siempre el del token, nunca uno del cuerpo.

### `POST /v1/teams`

Crea un equipo en una sola transacción; quien lo crea queda como su `admin`. El equipo nace en
modo `support` e idioma `en`. Cuerpo: `{name}` (un campo desconocido se rechaza).

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 201 | `{id}`; cabecera `Location: /v1/teams/{id}` | Equipo creado |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 401 | error `not_authenticated` | Sin token válido |
| 422 | error `validation_error` | Falta `name`, no es texto o hay un campo desconocido |
| 422 | error `invalid_team_name` | El nombre está en blanco o es demasiado largo una vez recortado |

### `GET /v1/teams`

Los equipos del usuario, con su rol en cada uno, ordenados por nombre sin distinguir mayúsculas.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `[{id, name, role}]` (vacía si no tiene equipos) | Siempre que hay sesión |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 401 | error `not_authenticated` | Sin token válido |

### `GET /v1/teams/{team_id}`

Un equipo del usuario: nombre, modo, idioma y el rol de quien pregunta.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `{id, name, mode, language, role}` | El usuario es miembro activo |
| 400 / 404 | error `tenant_required` / `tenant_not_found` | Tenant ausente o inválido |
| 401 | error `not_authenticated` | Sin token válido |
| 403 | error `not_a_team_member` | No es miembro: ajeno, retirado o inexistente (la misma respuesta) |
| 422 | error `validation_error` | `team_id` no es un UUID |

## Ceremonias (contrato del worker)

Definidas en el Sprint 0; se implementan con HU-56. Mientras tanto responden `501`. Por ahora no
exigen tenant ni sesión.

### `GET /v1/ceremonies/{ceremony_id}/context`

El contexto que el worker necesita antes de entrar a la sala.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | `CeremonyContext` (contrato en `shared/`) | Aún no ocurre |
| 422 | error `validation_error` | `ceremony_id` no es un UUID |
| 501 | error `not_implemented` | Siempre, hasta HU-56 |

### `POST /v1/ceremonies/{ceremony_id}/result`

El resultado que el worker entrega al cerrar la ceremonia. Cuerpo: `CeremonyResult`.

| Estado | Cuerpo | Cuándo |
| --- | --- | --- |
| 200 | — | Aún no ocurre |
| 422 | error `validation_error` | `ceremony_id` no es un UUID o el cuerpo no cumple el contrato |
| 501 | error `not_implemented` | Siempre, hasta HU-56 |
