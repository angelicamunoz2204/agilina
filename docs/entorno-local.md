# Entorno local

Todo corre en contenedores: lo único que necesitas en tu máquina es **Docker con
Compose** y **make** (más `bash`, `curl` y `openssl`, que cualquier Linux o macOS
ya trae). No se instala Python, uv, Node ni nada más.

## Qué corre dónde

| Pieza | Contenedor | Dónde escucha | Cuándo |
| --- | --- | --- | --- |
| Postgres | `postgres` | `localhost:5432` | `make up` |
| pgAdmin (cliente web de la base) | `pgadmin` | `localhost:5051` (solo desde tu máquina) | `make up` |
| Keycloak | `keycloak` | `localhost:8080`, sondas en `:9000` | `make up` |
| Mailpit (correo de pruebas) | `mailpit` | Bandeja en `localhost:8025`, SMTP en `:1025` | `make up` |
| API | `api` | `localhost:8000`, documentación en `/docs` | `make up` |
| Aplicación web | `web` | `localhost:4200` | `make up` |
| Servicio de transcripción | `stt` | `localhost:8001` | `make stt` |
| Worker del agente | `agent` | Sin puerto: se conecta hacia afuera | `make agent` |

El código fuente se monta dentro de los contenedores de desarrollo: al guardar un
archivo, la API y la web se recargan solas, sin reconstruir nada. Reconstruir
solo hace falta cuando cambian las dependencias (`pyproject.toml`,
`package.json`); `make up` ya lo hace.

Mailpit atrapa todo correo que envíe la aplicación (por ejemplo el enlace de
activación de una invitación): nada sale de tu máquina y lo ves en
<http://localhost:8025>.

## Requisitos

- Docker con Compose (v2 o posterior)
- `make`, `bash`, `curl` y `openssl` (el `.env` se genera con `openssl` y el arranque espera a Keycloak con `curl`)

No hace falta `buildx`: las imágenes se construyen también con el *builder*
clásico de Docker.

## Primera vez

```bash
make up      # .env, imágenes, contenedores, espera y migraciones
```

`make up` crea el `.env` a partir de `.env.example` si no existe y le genera
claves locales aleatorias para Postgres y para el administrador de Keycloak, de
modo que el repositorio no necesita guardar ninguna. Las claves de LiveKit,
ElevenLabs y Gemini las completas tú: sin ellas la API y la web funcionan, pero
el worker no entra a ninguna sala. La primera ejecución descarga y construye las
imágenes y tarda varios minutos; las siguientes son rápidas.

Los ganchos de git (`make hooks`) son opcionales y necesitan
[pre-commit](https://pre-commit.com) en tu máquina. La CI ejecuta las mismas
verificaciones, y `make verify` las corre en contenedores.

## Si ya tenías un `.env`

Desde HU-02 las variables y los objetivos de `make` están en inglés. `make env`
no sobrescribe un `.env` existente (solo le agrega las variables nuevas y genera las claves
que falten): renómbralo y deja que `make env` genere uno nuevo, o cambia los nombres a mano
según `.env.example` (por ejemplo
`POSTGRES_USUARIO` → `POSTGRES_USER`, `POSTGRES_CLAVE` → `POSTGRES_PASSWORD`,
`AGILINA_URL_BD` → `AGILINA_DB_URL`, `AGILINA_NIVEL_LOG` → `AGILINA_LOG_LEVEL`).
La contraseña de Postgres debe seguir siendo la misma si conservas el volumen.

Dentro de la red de contenedores los servicios se alcanzan por nombre
(`postgres`, `keycloak`, `stt`, `api`): el compose ya sobrescribe esas variables
para los contenedores, de modo que el `.env` sigue apuntando a `localhost`.

## Ver la base de datos con pgAdmin

pgAdmin viene con el entorno: <http://localhost:5051>. Escucha solo en tu máquina
(`127.0.0.1`), porque puede leer y cambiar toda la base.

- **Credenciales:** `make credentials` las imprime todas (Postgres, pgAdmin y Keycloak).
  Las de pgAdmin son `PGADMIN_ADMIN_EMAIL` y `PGADMIN_ADMIN_PASSWORD` del `.env`; la clave
  la genera `make env`. Es la cuenta de pgAdmin, no la de Postgres.
- **El servidor «Agilina» ya está registrado** y conecta sin pedir la contraseña de
  Postgres: la lee de un archivo que el Compose genera a partir del `.env`. Las tablas
  están en *Servers → Agilina → Databases → agilina → Schemas → public → Tables*.
- **Puerto de Postgres:** `5432` en tu máquina (`POSTGRES_PORT`), para un cliente de
  escritorio con servidor `localhost`. Dentro de la red de Compose es `postgres:5432`.
- El servidor se registra solo la primera vez que arranca pgAdmin con su volumen vacío. Si
  cambias `POSTGRES_USER` o `POSTGRES_DB` después, bórralo con `make clean` (o borra el
  volumen `agilina_pgadmin-data`).
- Si `make credentials` no muestra `PGADMIN_*`, `make env` las agrega a un `.env` anterior.

## Tenants: las organizaciones ([AD-29](adr/0029-un-tenant-es-una-organizacion-con-su-base-y-su-realm.md))

Un **tenant** es una organización que usa Agilina y contiene equipos. Cada uno tiene **su propia
base de datos, su propio realm de Keycloak y su propio login**: una misma persona en dos tenants
tiene dos cuentas. `make up` deja dos de desarrollo:

| Tenant (*slug*) | Organización | Idioma | Base de datos | Realm | Dirección de la web |
| --- | --- | --- | --- | --- | --- |
| `acme` | ACME Corporation | inglés | `agilina_acme` | `agilina-acme` | <http://localhost:4200/acme> |
| `ecomoda` | Ecomoda | español | `agilina_ecomoda` | `agilina-ecomoda` | <http://localhost:4200/ecomoda> |

El tenant es el **primer segmento de la dirección** de la web (`/acme/teams`) y el encabezado
`X-Agilina-Tenant` de cada llamada a la API. Sin él, la API responde `400 tenant_required`; con un
tenant que no existe, que está suspendido o que ni siquiera es un nombre válido, responde siempre el
mismo `404 tenant_not_found`; y `http://localhost:4200/` no nombra ninguna organización y se ve como
«no encontrada». Solo `/health` y la documentación no piden tenant. Un token de un tenant no vale en
otro (`401`): su emisor es el de su realm.

```bash
curl -i localhost:8000/v1/teams                                  # 400 tenant_required
curl -i -H 'X-Agilina-Tenant: acme' localhost:8000/v1/tenant     # 200: slug, nombre e idioma
curl -i -H 'X-Agilina-Tenant: nadie' localhost:8000/v1/tenant    # 404 tenant_not_found
```

Dónde está cada cosa: el catálogo de tenants es la base `agilina_platform` (tabla `tenant`, y los
trabajos programados); `pgAdmin` ve todas. Los nombres salen del *slug* (prefijos
`AGILINA_TENANT_DB_PREFIX` y `AGILINA_TENANT_REALM_PREFIX`), y el secreto del cliente `agilina-api` de
cada realm está en el `.env` como `AGILINA_TENANT_<SLUG>_KEYCLOAK_API_SECRET` (uno por tenant).

**Agregar un tenant** lo hace el administrador (hoy, quien desarrolla), con un comando; no hay panel:

```bash
make tenant-add slug=wonka name="Wonka Industries" lang=en
```

Crea y migra su base, crea su realm desde `infra/keycloak/realm-template.json`, genera su secreto en el
`.env` (y reinicia la API para que lo lea) y lo escribe en el catálogo. Se puede repetir sin problema.
`slug`: letras minúsculas y dígitos, de 2 a 31 caracteres, empieza con letra (`platform`, `admin` y `api`
están reservados). **Suspender, reactivar o renombrar** es un `UPDATE` directo en el catálogo:

```sql
UPDATE tenant SET status = 'suspended' WHERE slug = 'wonka';   -- tarda hasta 30 s en notarse
```

`make migrate` crea y migra el catálogo y la base de **todos** los tenants (suspendidos incluidos);
`make migration m="…"` crea una migración vacía del esquema de los tenants y
`make migration-platform m="…"` una del catálogo.

## Invitar a alguien y activar su cuenta (HU-02)

No hay registro público: la primera persona de un equipo la invita el operador de la
plataforma (AD-22), con el entorno levantado (`make up`):

```bash
make invite tenant=acme team="Atlas" email=julian@example.com name="Julián Torres"
make invite tenant=ecomoda team_id=<uuid> email=laura@example.com name="Laura Méndez" role=member   # a un equipo que ya existe
```

Crea el equipo en ese tenant (sin autor: lo creó el operador) y la invitación, y envía el correo, en
el idioma del tenant salvo que des `lang=`; con Mailpit lo ves en <http://localhost:8025>. El enlace
(`…/acme/activate#t=<token>`) lleva el tenant y abre la pantalla de activación de la web
(<http://localhost:4200/acme/activate>): comprueba el enlace, pide la
contraseña con su confirmación y, al activar, lleva a Keycloak con el correo ya escrito. La
web lee el token del fragmento, lo quita de la barra de direcciones y llama a la API:

| Operación | Qué hace |
| --- | --- |
| `POST /v1/invitations/status` | Qué muestra la página: correo y nombre si el enlace sirve; `410` si ya se usó, venció o fue revocado; `404` si fue alterado |
| `POST /v1/invitations/activate` | Con `token`, `password` y `confirmation`: crea la cuenta en Keycloak, el usuario y la membresía; `201`. `422` si la contraseña no coincide o incumple la política (con los motivos), `409` si el correo ya tiene cuenta |
| `POST /v1/invitations/request-new` | Avisa por correo a los administradores del equipo; `202`. `409` si el enlace aún sirve |

El token va en el cuerpo, nunca en la URL, y ninguna respuesta lo repite. La
documentación interactiva está en <http://localhost:8000/docs>. Todos los fallos
responden `{"code": …}` con un código estable (`invitation_expired`, `password_policy`…).

La política de contraseñas es la de Keycloak: mínimo 12 caracteres, distinta del correo
(AD-24); la pantalla muestra esa misma regla y los motivos que la API devuelve. Al terminar,
la web lleva a iniciar sesión (HU-03) en el realm de ese tenant. La API crea la cuenta con su propia
cuenta de servicio, `agilina-api`, en el realm del tenant, con el secreto de ese tenant que genera
`make env` o `make tenant-add`.

### Si cambias el realm de Keycloak

Mientras el desarrollo sea local, ni los realms ni las migraciones se parchean con *scripts* de
actualización: se cambia la plantilla (o la migración inicial) y se reconstruye desde cero. Para
empezar todo de nuevo, `make clean` y `make up` (borra las bases, los usuarios de Keycloak y las
imágenes locales); para empezar solo Keycloak de nuevo, `make keycloak-reset`.

Los realms salen de la plantilla `infra/keycloak/realm-template.json` cuando se crea el tenant
(`make tenant-add`): un cambio de la plantilla no llega a un realm que ya existe. Para aplicarlo en
un entorno que ya existía:

```bash
make keycloak-reset    # borra los datos de Keycloak (no los de Postgres) y recrea el realm de cada tenant
```

`make test-keycloak` ejecuta las pruebas contra ese Keycloak real.

## Crear equipos (HU-05)

Cualquier usuario autenticado puede crear un equipo, y queda como su Administrador. La API:

| Operación | Qué hace |
| --- | --- |
| `POST /v1/teams` | Con `{"name": …}`: crea el equipo y la membresía de quien lo pide como `admin`, en una sola transacción (si algo falla, no queda nada guardado); `201` con `{"id": …}` y `Location: /v1/teams/<id>` |
| `GET /v1/teams` | Los equipos donde el usuario es integrante activo, con `id`, `name` y su `role` en cada uno, ordenados por nombre sin distinguir mayúsculas; `[]` si no tiene ninguno |
| `GET /v1/teams/{team_id}` | `name`, `mode` y `language` del equipo y el `role` de quien pregunta; solo para sus integrantes activos |

Las tres exigen `Authorization: Bearer <token>`, y quien crea el equipo es siempre el
usuario del token, nunca uno que venga en el cuerpo. Los errores responden
`{"code": …}`, como el resto de la API:

| Código | Cuándo |
| --- | --- |
| `401 not_authenticated` | Sin token o con uno que no identifica a un usuario de Agilina. Lleva `WWW-Authenticate: Bearer` y se responde antes de mirar el equipo |
| `403 not_a_team_member` | `GET /v1/teams/{team_id}` de un equipo ajeno, de uno del que te removieron o de uno que no existe: es la misma respuesta en los tres casos, para no revelar qué equipos existen |
| `422 invalid_team_name` | El nombre queda vacío o pasa de 80 caracteres después de recortarlo |

Un cuerpo mal formado (sin `name`, o con un campo desconocido como `created_by`) y un
`team_id` que no es un UUID también responden `422`, pero con el formato de validación de
FastAPI, sin `code`.

Todas piden además el encabezado `X-Agilina-Tenant`. La web tiene tres pantallas dentro de cada
tenant: `/acme/teams` (el selector: la lista de tus equipos y «Crear equipo»; con un solo equipo, entra
directo a él), `/acme/teams/new` (el formulario) y `/acme/teams/:teamId` (el dashboard del equipo, que
por ahora solo muestra su nombre; el real llega con HU-12).

### Valores por defecto de un equipo nuevo

Un equipo que crea una persona con `POST /v1/teams` nace así:

| Dato | Valor | Notas |
| --- | --- | --- |
| Modo (`mode`) | `support` | Soporte: un Scrum Master humano aprueba lo que hace Agilina |
| Idioma (`language`) | `en` | Se guarda el código (`en` o `es`); «English» es solo la etiqueta de la interfaz |
| Rol de quien lo crea | `admin` | Además queda registrado como su autor (`created_by`) |
| Nombre (`name`) | Obligatorio | Se recorta; si queda vacío no vale; máximo 80 caracteres, que la base también exige (`CHECK team_name_max_length`). Dos equipos pueden llamarse igual |

Estos valores también aparecen en la descripción de la operación en
<http://localhost:8000/docs>, y el formulario de la web avisa que el equipo se crea en modo
soporte e idioma inglés.

El equipo que crea el **operador** con `make invite tenant=… team=…` es distinto: también nace en
`support`, pero su idioma es el de `lang=` o, si no lo das, el del tenant. No tiene autor ni integrantes: la primera persona entra cuando
activa su invitación, con el rol de esa invitación (AD-22).

### Cómo probarlo

Con el entorno levantado (`make up`), este es el camino desde cero:

1. `make invite tenant=acme team="Atlas" email=ana@example.com name="Ana Ruiz"` crea el equipo del
   operador en `acme` y la invitación de su primera Administradora.
2. En Mailpit (<http://localhost:8025>) abre el correo y pulsa el botón: llegas a
   `/acme/activate`.
3. Elige una contraseña de 12 o más caracteres. Esto crea a la vez la cuenta en el realm de `acme` y el
   usuario de Agilina en la base de `acme` (`app_user`), y la deja como `admin` de «Atlas». La web te
   lleva a iniciar sesión.
4. Entras a `/acme/teams/<id>`: con un solo equipo, el selector entra directo. Con «Crear equipo» (desde
   `/acme/teams/new`) tendrás dos, y `/acme/teams` mostrará el selector.
5. Para ver el aislamiento entre equipos, invita y activa a otra persona en otro equipo: si pide
   `GET /v1/teams/<id de Atlas>` con su token, recibe `403 not_a_team_member`. Y entre tenants: la misma
   dirección con `ecomoda` en lugar de `acme` pide iniciar sesión en el realm de Ecomoda, donde esa
   persona no tiene cuenta.

- **Pruebas automatizadas.**
  - `make test-integration` corre la API real contra PostgreSQL: los equipos
    (`tests/api/integration/teams/`) y el aislamiento entre tenants contra dos bases reales
    (`tests/api/integration/shared/presentation/http/test_multitenancy_flow.py`).
  - `make test-web` prueba los componentes con el Router real y un puerto falso.
  - `make test-e2e` recorre todo en un navegador, en los dos tenants.
- **Swagger** (<http://localhost:8000/docs>). La sección *teams* muestra el contrato, los valores por
  defecto y el esquema de seguridad `HTTPBearer`. El encabezado de tenant está explicado en la
  descripción de la API.

### Iniciar sesión (HU-03)

La web lleva al login de **Keycloak** (<http://localhost:8080>), con su tema propio y el correo ya
escrito si vienes de la activación. La contraseña solo la ve Keycloak: nunca la web ni la API. Entra
cualquier persona activada:

- <http://localhost:4200/acme> manda a iniciar sesión en el realm de `acme` (o, con sesión, a tus
  equipos; con un solo equipo, directo a él). <http://localhost:4200/> no nombra ninguna organización.
- Una página que pide sesión (por ejemplo `/acme/teams/<id>`) te lleva a iniciar sesión y te devuelve
  a ella.
- La sesión es **por tenant**: estar dentro de `acme` no te mete en `ecomoda`.
- Un correo o una contraseña incorrectos dan **el mismo mensaje**, exista o no el correo, y tras
  varios intentos fallidos Keycloak bloquea la cuenta un rato.
- El idioma de la página de login es el de la web (el del navegador); si se abre sin eso, es el del
  tenant (`acme` en inglés, `ecomoda` en español).
- Son públicas, sin sesión: `/acme/activate` (el enlace de la invitación) y `/acme/status`.

La API valida el token de Keycloak en cada petición protegida (firma, emisor, audiencia y vigencia) y
responde `401 not_authenticated` si no sirve. Para probarla con un token real, ver `make test-keycloak`.

Tras un cambio de la plantilla del realm hay que correr `make keycloak-reset`, **que borra los usuarios
de Keycloak de desarrollo (de todos los realms)**: las cuentas activadas antes quedan sin su usuario en
Keycloak y hay que volver a invitar con `make invite`.

#### El tema del login

El aspecto de esa página está en `infra/keycloak/themes/agilina/login/` (plantillas FreeMarker con
clases de Tailwind y los textos en `messages_es.properties` / `messages_en.properties`). Usa los mismos
tokens de diseño que la web (`web/src/tokens.css`) y se compila al construir la imagen de Keycloak
(`infra/docker/keycloak.Dockerfile`). Tras cambiarlo:

```bash
make keycloak-theme    # reconstruye la imagen y reinicia solo Keycloak (conserva sus datos)
```

#### Pruebas de punta a punta

```bash
make up           # el entorno tiene que estar levantado
make test-e2e     # invita a una persona nueva a un equipo nuevo de cada tenant y recorre, en un navegador
                  # real (Playwright), invitar → activar → iniciar sesión → entrar al equipo → volver a la
                  # página pedida, y que los tenants no se mezclan
```

Corren en un contenedor sobre la red del anfitrión (Linux), con el entorno de `make up`.

### El usuario de desarrollo

La plantilla del realm no trae ninguna persona, y no se le agrega: AD-22 descarta sembrar una
cuenta con credenciales en el repositorio. Además, una cuenta que existe solo en Keycloak
no sirve, porque Agilina necesita también su `app_user` y su membresía. El camino
`make invite` → Mailpit → activación crea las dos cosas, se repite cuando haga falta y no
deja ningún secreto en el repositorio.

## Entrar a Keycloak

La consola de administración está en <http://localhost:8080/admin> (con el
entorno levantado: `make up` o `make infra`). Las credenciales están en tu
`.env`, que git ignora y `make env` genera la primera vez:

| Dato | Variable del `.env` | Valor |
| --- | --- | --- |
| Usuario | `KEYCLOAK_ADMIN` | `admin` |
| Contraseña | `KEYCLOAK_ADMIN_PASSWORD` | Aleatoria, generada por `make env` |

**Cómo ver la contraseña:** desde la carpeta del repo, ejecuta

```bash
grep KEYCLOAK_ADMIN .env
```

Imprime las dos líneas, `KEYCLOAK_ADMIN=admin` y
`KEYCLOAK_ADMIN_PASSWORD=<la contraseña>`; la contraseña es lo que va después del
`=`. También puedes abrir el archivo `.env` y buscar esa variable. Para ver
solo la contraseña:

```bash
grep '^KEYCLOAK_ADMIN_PASSWORD=' .env | cut -d= -f2
```

Entras al realm `master`, que es el de administración; los de Agilina son uno por tenant
(`agilina-acme`, `agilina-ecomoda`…) y se eligen en el menú de arriba a la izquierda. Este usuario
administra Keycloak, no es una persona de Agilina. Los realms de los tenants no tienen ninguna persona:
solo los clientes `agilina-web`, `agilina-worker` y `agilina-api`, y las cuentas de servicio de los dos
últimos (la del worker y la que usa la API para crear cuentas). Las personas llegan con las
invitaciones (HU-02; ver «El usuario de desarrollo»).

La contraseña solo se aplica cuando Keycloak se crea por primera vez, con su
volumen de datos vacío. Si cambias `KEYCLOAK_ADMIN_PASSWORD` después, Keycloak
sigue con la anterior: para empezar de cero, `make clean` y `make up` (borra los
datos de Postgres y de Keycloak). Si el `.env` se perdió, hay que hacer lo mismo,
porque `make env` generaría una contraseña nueva que no coincide con la que ya
guardó el volumen.

## Correo

Todo correo que envía la aplicación (por ejemplo el enlace de activación de una
invitación) sale por SMTP, y **qué servidor lo entrega es solo configuración**
(AD-23). Por defecto es **Mailpit**: atrapa los mensajes y los muestra en
<http://localhost:8025>; nada sale de tu máquina. Es lo que usan el desarrollo y la CI.

Para comprobar el envío en cualquier momento (con `make up` o `make infra` activos):

```bash
make mail-test to=alguien@example.com            # en el idioma por defecto
make mail-test to=alguien@example.com lang=en    # en inglés (lang=es o lang=en)
```

Con Mailpit, el mensaje aparece en su bandeja; la dirección puede ser cualquiera. Es un
correo con el diseño real (HTML) y su versión de texto: en Mailpit puedes alternar entre
las pestañas *HTML*, *Text* y *HTML Source*, y ver cómo se adapta a un ancho de móvil.

### Plantillas de correo

Los correos no llevan texto escrito en el código: se arman con plantillas en
`api/src/agilina_api/shared/infrastructure/mail/`.

| Archivo | Qué es |
| --- | --- |
| `templates/layout.html` | El marco común: cabecera con la marca, tarjeta de contenido y pie |
| `templates/<nombre>.html` | El contenido de un correo; extiende el marco |
| `templates/<nombre>.txt` | La versión de texto plano, que muestran los clientes sin HTML |
| `texts.py` | Todos los textos, en español y en inglés |
| `theme.py` | Los colores y las tipografías |

Para ver un cambio de diseño: edita la plantilla, ejecuta `make mail-test to=...` y
abre Mailpit (la API recarga sola, y el comando renderiza la plantilla en cada
ejecución). Reglas del diseño: los colores y las tipografías **son los tokens de los mockups**
(`context/mockups.md`: índigo `#3b5bd4`, tarjeta blanca sobre fondo azul pálido,
Plus Jakarta Sans e Inter) y viven solo en `theme.py`; una prueba los reconvierte desde
los valores originales del mockup y falla si uno se desvía. Además, tema oscuro con
`prefers-color-scheme` para los clientes que lo soportan. Sin imágenes ni hojas de estilo
remotas (los clientes de correo las bloquean), estilos en línea y maquetación con tablas;
por eso el logo es la inicial «A» sobre un cuadrado índigo y no el icono del mockup. Los valores que entran
en el HTML se escapan solos, y un parámetro que falta hace fallar el envío en vez de
mandar un correo a medias.

### Cambiar a Amazon SES (sandbox)

Sirve para una demo con correo real o para probar el camino de producción. Los pasos de
la consola de AWS son los que conozco; confírmalos allí.

1. En la consola de **SES**, elige la región (la misma donde se desplegará; el servidor
   SMTP depende de ella).
2. **Identities → Create identity → Email address**, para la dirección que será el
   remitente y para cada destinatario de prueba (tú, Diego…). Cada una recibe un correo
   con un enlace de verificación. En *sandbox*, SES solo entrega a identidades verificadas.
3. **SMTP settings → Create SMTP credentials.** Crea un usuario de IAM y muestra su
   usuario y contraseña SMTP **una sola vez**; no son las de tu cuenta de AWS.
4. En tu `.env` (nunca en el repositorio):

   ```bash
   AGILINA_SMTP_HOST=email-smtp.<región>.amazonaws.com
   AGILINA_SMTP_PORT=587
   AGILINA_SMTP_USER=<usuario SMTP>
   AGILINA_SMTP_PASSWORD=<contraseña SMTP>
   AGILINA_SMTP_SECURITY=starttls
   AGILINA_MAIL_FROM='Agilina <la-direccion-verificada>'
   ```
5. `make restart` (la API lee el `.env` al crearse) y luego
   `make mail-test to=<una dirección verificada>`. Si dice «Not sent», revisa la región,
   la verificación de las dos direcciones y las credenciales.

Límites mientras no haya dominio propio: *sandbox* (cerca de 200 correos por día y solo a
destinatarios verificados) y, como el remitente no tiene SPF ni DKIM propios, los correos
pueden llegar a spam. Salir del *sandbox* y enviar a cualquiera se pide en AWS y requiere
un dominio verificado: llega con el despliegue (HU-38).

Para **volver a Mailpit**, restaura esas variables a los valores de `.env.example`
(servidor `mailpit`, puerto `1025`, sin usuario ni contraseña, seguridad `none`) y
`make restart`.

## El secreto del worker

Los realms de los tenants se crean desde `infra/keycloak/realm-template.json` y el
secreto del cliente `agilina-worker` de cada uno lo genera Keycloak: no está en el
repositorio. (Cómo el worker elige su tenant se define con HU-55.) Para obtenerlo:

1. Entra a la consola de Keycloak (ver la sección anterior).
2. Realm `agilina-acme` (o el del tenant) → Clients → `agilina-worker` → pestaña Credentials.
3. Copia el secreto en `AGILINA_KEYCLOAK_WORKER_SECRET` de tu `.env` y ejecuta `make agent`.

## Trabajar sin GPU

El servicio de transcripción arranca en modo simulado
(`AGILINA_STT_SIMULATED=true`): responde con texto de prueba sin descargar el
modelo. Es lo que permite ejercitar la ceremonia completa en un portátil y lo
que mantiene el pipeline por debajo de los diez minutos.

La imagen con CUDA para transcribir de verdad llega con el despliegue en la nube
(HU-38); hoy el modo con GPU solo existe en el spike de voz (HU-01).

## Comandos frecuentes

```bash
make                # lista todos los objetivos
make up             # construye, levanta todo, espera y migra
make down           # detiene los contenedores sin borrar datos
make credentials    # URLs y credenciales de Postgres, pgAdmin y Keycloak
make logs s=api     # logs de un servicio (sin s=, de todos)
make ps             # qué está corriendo
make migrate        # crea y migra el catálogo y la base de cada tenant
make mail-test to=a@b.com   # envía un correo de prueba con el SMTP configurado
make migration m="crear tabla equipos"   # migración vacía del esquema de los tenants: se escribe a mano, en SQL
make migration-platform m="…"            # lo mismo, del catálogo de tenants
make tenant-add slug=wonka name="Wonka Industries" lang=en   # agrega un tenant (base, realm y catálogo)
make tenants-dev                         # asegura los tenants de desarrollo (acme y ecomoda); se repite sin problema
make tenant-realms                       # crea el realm de cada tenant del catálogo que no lo tenga
make test           # pruebas de Python, de integración (PostgreSQL real) y de la web
make test-integration   # solo las de integración: levanta Postgres y usa una base temporal
make test-keycloak      # pruebas contra el Keycloak real (levanta Keycloak y lo espera)
make test-e2e           # pruebas de punta a punta en un navegador real (con el entorno levantado)
make keycloak-reset     # Keycloak desde cero y el realm de cada tenant (borra sus datos y sus usuarios)
make keycloak-theme     # reconstruye el tema de login de Keycloak y reinicia solo Keycloak
make invite tenant=… team=… email=… name=…   # crea un equipo en un tenant e invita a su primer administrador
make lint           # ruff y ESLint
make format         # ruff format y Prettier (la web)
make typecheck      # mypy en modo estricto
make arch           # reglas de arquitectura (capas y fronteras entre contextos)
make verify         # exactamente lo que corre el pipeline, en contenedores
make lock           # actualiza uv.lock y package-lock.json tras cambiar dependencias
make clean          # borra contenedores, volúmenes, imágenes y cachés
```

## Cuando algo falla

| Síntoma | Causa habitual |
| --- | --- |
| `make up` dice que un puerto está ocupado | Otro servicio usa 5432, 8000, 8080, 4200, 8025 o 1025. Detenlo o cambia el puerto en el `.env` (`POSTGRES_PORT`, `AGILINA_API_PORT`, `MAILPIT_UI_PORT`…) |
| `make migrate` falla con conexión rechazada | Postgres todavía arranca: `make logs s=postgres` y reintenta |
| `make agent` pide completar el `.env` | Faltan `AGILINA_LIVEKIT_URL`, `AGILINA_LIVEKIT_API_KEY` y `AGILINA_LIVEKIT_API_SECRET`: el worker no arranca sin ellos |
| La web muestra «No disponible» | La API no está corriendo: `make logs s=api` |
| Un tenant no tiene realm en Keycloak | Keycloak perdió sus datos o el tenant se agregó sin él: `make tenant-realms` |
| Cambié `package.json` o `pyproject.toml` y la imagen no se construye ("lockfile needs to be updated" o `npm ci` falla) | Ejecuta `make lock`, commitea los dos locks y repite `make up` |
| Los archivos que crea un contenedor son de `root` | El compose usa tu usuario (`HOST_UID`/`HOST_GID`); ejecuta siempre con `make`, no con `docker compose` a mano |
