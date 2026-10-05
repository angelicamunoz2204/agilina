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

Entras al realm `master`, que es el de administración; el de Agilina es
`agilina` y se elige en el menú de arriba a la izquierda. Este usuario administra
Keycloak, no es una persona de Agilina: el realm `agilina` solo tiene la cuenta
de servicio del worker, y las personas llegan con las invitaciones (HU-02).

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

El realm de Keycloak se importa desde `infra/keycloak/realm-agilina.json` y el
secreto del cliente `agilina-worker` lo genera Keycloak: no está en el
repositorio. Para obtenerlo:

1. Entra a la consola de Keycloak (ver la sección anterior).
2. Realm `agilina` → Clients → `agilina-worker` → pestaña Credentials.
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
make migrate        # aplica las migraciones pendientes
make mail-test to=a@b.com   # envía un correo de prueba con el SMTP configurado
make migration m="crear tabla equipos"   # migración vacía de Alembic: se escribe a mano, en SQL
make test           # pruebas de Python, de integración (PostgreSQL real) y de la web
make test-integration   # solo las de integración: levanta Postgres y usa una base temporal
make lint           # ruff y ESLint
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
| Keycloak no importa el realm | El volumen ya tenía datos: `make clean` y `make up` |
| Cambié `package.json` o `pyproject.toml` y la imagen no se construye ("lockfile needs to be updated" o `npm ci` falla) | Ejecuta `make lock`, commitea los dos locks y repite `make up` |
| Los archivos que crea un contenedor son de `root` | El compose usa tu usuario (`HOST_UID`/`HOST_GID`); ejecuta siempre con `make`, no con `docker compose` a mano |
