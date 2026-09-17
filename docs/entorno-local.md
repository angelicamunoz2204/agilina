# Entorno local

## Qué corre dónde

| Pieza | Cómo corre | Dónde escucha |
| --- | --- | --- |
| Postgres | Contenedor (`make infra`) | `localhost:5432` |
| Keycloak | Contenedor (`make infra`) | `localhost:8080`, sondas en `:9000` |
| API | Proceso local (`make api`) | `localhost:8000`, documentación en `/docs` |
| Servicio de transcripción | Proceso local (`make stt`) | `localhost:8001` |
| Worker del agente | Proceso local (`make agent`) | Sin puerto: se conecta hacia afuera |
| Aplicación web | Proceso local (`make web`) | `localhost:4200` |

La base de datos y la identidad van en contenedores porque nadie las edita; los
cuatro desplegables corren como procesos locales porque se editan todo el
tiempo y la recarga automática es la diferencia entre iterar y esperar. La
contenerización de los cuatro llega con el despliegue en la nube (HU-38).

## Requisitos

- Docker con Compose
- [uv](https://docs.astral.sh/uv/) para Python
- Node 22 y npm para la aplicación web
- `make`

En macOS: `brew install uv node` y Docker Desktop.

## Primera vez

```bash
make arriba      # .env, dependencias, contenedores y migraciones
make ganchos     # instala los ganchos de pre-commit (una vez por clon)
```

`make arriba` crea el `.env` a partir de `.env.example` si no existe y le
genera claves locales aleatorias para Postgres y para el administrador de
Keycloak, de modo que el repositorio no necesita guardar ninguna. Las claves de
LiveKit, ElevenLabs y Gemini las completas tú: sin ellas la API y la web
funcionan, pero el worker no entra a ninguna sala.

## El secreto del worker

El realm de Keycloak se importa desde `infra/keycloak/realm-agilina.json` y el
secreto del cliente `agilina-worker` lo genera Keycloak: no está en el
repositorio. Para obtenerlo:

1. Entra a <http://localhost:8080/admin> con las credenciales de tu `.env`.
2. Realm `agilina` → Clients → `agilina-worker` → pestaña Credentials.
3. Copia el secreto en `AGILINA_KEYCLOAK_SECRETO_WORKER` de tu `.env`.

## Trabajar sin GPU

El servicio de transcripción arranca en modo simulado
(`AGILINA_STT_SIMULADO=true`): responde con texto de prueba sin descargar el
modelo. Es lo que permite ejercitar la ceremonia completa en un portátil y lo
que mantiene el pipeline por debajo de los diez minutos.

Con GPU disponible:

```bash
uv sync --package agilina-stt --extra gpu
AGILINA_STT_SIMULADO=false AGILINA_STT_DISPOSITIVO=cuda make stt
```

## Comandos frecuentes

```bash
make              # lista todos los objetivos
make verificar    # exactamente lo que corre el pipeline, en tu máquina
make pruebas      # solo las pruebas
make migracion m="crear tabla equipos"   # nueva migración de Alembic
make migrar       # aplica las migraciones pendientes
make logs         # logs de Postgres y Keycloak
make abajo        # detiene los contenedores sin borrar datos
make limpiar      # borra cachés, dependencias y datos de los contenedores
```

## Cuando algo falla

| Síntoma | Causa habitual |
| --- | --- |
| `make migrar` falla con conexión rechazada | Postgres todavía arranca: `make logs` y reintenta |
| La web muestra «No disponible» | La API no está corriendo: `make api` |
| Keycloak no importa el realm | El volumen ya tenía datos: `make limpiar` y `make arriba` |
| `uv sync` no encuentra `agilina-shared` | Ejecútalo desde la raíz del repositorio, no desde una carpeta |
| Las pruebas de la web no arrancan | Falta Chrome; instálalo o usa `npm test` con tu navegador |
