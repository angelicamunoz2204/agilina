# AD-29: un tenant es una organización, con su propia base de datos, su realm y su login

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-07
- **Deciden:** Diego, Angélica
- **Historia:** ninguna; arquitectura (Sprint-0)
- **Supersede en parte a:** AD-21 («el equipo es el tenant») y AD-28 (un solo realm)

## Contexto

La propuesta del proyecto contempla la multitenencia. Hasta ahora el repositorio la trataba
como «el equipo es el tenant»: una sola base de datos, un solo realm de Keycloak y el
aislamiento por `team_id`. Eso aísla equipos, pero no organizaciones: dos empresas que usen
Agilina compartirían usuarios, login y base. Es un proyecto educativo sin balanceadores ni panel
de administración de tenants, pero la solución debe modelarse multitenant desde ahora, porque
las cuentas, los tokens y el emisor dependen de esta decisión y cambiarla después es caro. Dos
tenants de prueba bastan para demostrarla.

## Decisión

- **Un tenant es una organización** y contiene equipos. Cada tenant tiene **su propia base de
  datos** (`agilina_<slug>`), **su propio realm** de Keycloak (`agilina-<slug>`) y **su propio
  login**. Una misma persona en dos tenants tiene dos cuentas distintas. Dentro de un tenant, los
  equipos siguen aislados por `team_id` y una persona sigue pudiendo estar en varios (HU-05).
- **Un catálogo de tenants** en una base propia (`agilina_platform`): la tabla `tenant` (slug,
  nombre, idioma, estado) y los trabajos del planificador, con el tenant en cada uno. La base y
  el realm de un tenant no se guardan: salen del slug, para que el catálogo no pueda
  contradecirlos. El slug son letras minúsculas y dígitos (2 a 31, empieza con letra; `platform`,
  `admin` y `api` están reservados).
- **Cada petición nombra su tenant** en el encabezado `X-Agilina-Tenant`. Sin él, `400
  tenant_required`; un tenant que no existe, está suspendido o ni siquiera es un nombre válido es
  siempre el mismo `404 tenant_not_found`, para que nadie pueda listar los tenants. Solo `/health`
  y la documentación no lo necesitan. El token se valida contra **el realm de ese tenant**: un
  token de otro tenant es un `401`, porque su emisor no es el del encabezado.
- **La API crea un grafo de objetos por tenant** (`Container`: su motor de base de datos, su
  validador de tokens, su proveedor de identidad con su secreto) la primera vez que lo usa, y lo
  reutiliza. Todo lo que toca datos de un tenant llega por `current_container`, que depende de
  `current_tenant`: por eso ninguna ruta de datos puede olvidar el tenant. El dominio, los casos
  de uso, los repositorios y las consultas **no cambian**: el tenant se elige en el borde.
- **El catálogo se consulta con una caché de 30 s**; suspender un tenant (`UPDATE tenant SET
  status = 'suspended'`) tarda hasta ese tiempo en notarse.
- **La web lleva el tenant como primer segmento de la ruta** (`/acme/teams`): decide el realm
  con el que se inicia sesión y el encabezado de cada llamada. `/` no nombra ninguna organización
  y es una página «no encontrada», igual que un nombre que no puede ser un tenant y uno que
  parece válido pero no existe (la web lo comprueba con `GET /v1/tenant` antes de llevar a nadie
  a iniciar sesión en un realm que no está). Cada tenant tiene su sesión de `keycloak-js`.
- **El administrador (hoy, los desarrolladores) da de alta un tenant con `make tenant-add`:**
  crea la base y la migra, crea el realm desde `infra/keycloak/realm-template.json` con la API de
  administración de Keycloak, genera su secreto para el cliente `agilina-api` (en el `.env`, uno
  por tenant) y escribe su fila en el catálogo. Es idempotente y se puede repetir tras un fallo a
  medias. Suspender, reactivar o renombrar es un `UPDATE` del catálogo. No hay panel.
- **Migraciones en dos entornos de Alembic:** `tenant` (el esquema de cada base de tenant) y
  `platform` (el catálogo). `make migrate` aplica el del catálogo y después el de **todos** los
  tenants del catálogo, suspendidos incluidos, para que no se atrasen.
- **El idioma es un atributo del tenant** (`acme` en inglés, `ecomoda` en español): es el
  `defaultLocale` de su realm (la página de login), el idioma de `make invite` y el de los equipos
  nuevos hasta que un equipo elija el suyo. Los tenants de desarrollo son `acme` (ACME
  Corporation) y `ecomoda` (Ecomoda).

## Alternativas descartadas

- **Una sola base con `tenant_id` en cada tabla:** el aislamiento depende de que cada consulta
  filtre, y el catálogo de usuarios queda compartido. Una base por tenant hace que mezclar datos
  exija usar la conexión equivocada, que es más difícil de hacer sin querer.
- **Un solo realm, con *Organizations* de Keycloak o con grupos:** no separa el login, las
  políticas ni el emisor de cada organización, y deja a Keycloak y a la base como dos fuentes de
  verdad de a qué pertenece cada persona.
- **El tenant en un subdominio** (`acme.agilina.app`): es lo más realista en la nube, pero en
  desarrollo exige `acme.localhost` o DNS. El prefijo en la ruta funciona en `localhost` y se ve
  en el enlace del correo; pasar a subdominios es cambiar de dónde se lee el nombre.
- **Un `404` distinto para un tenant suspendido:** revelaría qué tenants existen.

## Consecuencias

- Una persona invitada a dos organizaciones tiene dos cuentas, con dos contraseñas: es el costo de
  separar los logins.
- Un pool de conexiones por tenant. Con dos no importa; el tamaño sigue siendo configurable.
- Las migraciones pueden desfasarse entre tenants si alguien migra a mano una sola base:
  `make migrate` recorre todas.
- Agregar un tenant exige reiniciar la API para que lea su secreto (`make tenant-add` lo hace).
- **`make keycloak-reset` borra los usuarios de todos los realms** y recrea los realms de los
  tenants del catálogo; las cuentas activadas antes quedan sin su usuario en Keycloak y hay que
  volver a invitar.
- El worker (HU-55) y la sala (LiveKit) heredarán la regla: el contexto de la ceremonia y el
  nombre de la sala llevarán el tenant.
- Los tenants se crean con una herramienta de línea de comandos y no con un panel; si el producto
  llegara a venderse, esa herramienta es lo que habría que convertir en servicio.

## Cómo se verifica

`make verify` (con la API al 100 % de cobertura) incluye las pruebas de aislamiento contra dos
bases reales: el mismo correo en dos tenants son dos usuarios, los equipos de uno no se ven desde
el otro, un token de un tenant da `401` en el otro y un tenant inexistente o suspendido da el
mismo `404`. `make test-keycloak` comprueba lo mismo contra dos realms reales, crea un realm desde
la plantilla y lo usa. `make test-e2e` recorre invitar → activar → iniciar sesión → equipo en un
navegador, en los dos tenants, con la misma persona.
