# Agilina

Scrum Master virtual que facilita la reunión diaria por voz: conduce la
ceremonia, cede la palabra, registra lo hablado y, al cerrar, convierte la
conversación en artefactos accionables sobre las herramientas donde el equipo
ya trabaja.

Opera en dos modos. En **modo soporte** hay un Scrum Master humano que la
supervisa y Agilina pide aprobación antes de ejecutar una acción. En **modo
autónomo** el equipo ha alcanzado la madurez para prescindir del rol y Agilina
asume la facilitación completa.

Trabajo integrador de la Maestría en Computación para el Desarrollo de
Aplicaciones Inteligentes, Universidad del Valle. Diego Bonilla y Angélica
Muñoz; asesor: Oscar Bedoya.

## Levantar el entorno

```bash
git clone git@github.com:angelicamunoz2204/agilina.git && cd agilina
make arriba
```

`make arriba` crea el `.env` con claves locales generadas, instala las
dependencias de Python y de la web, levanta Postgres y Keycloak, espera a que
respondan y aplica las migraciones.
Después, en terminales separadas:

```bash
make api     # http://localhost:8000/docs
make stt     # http://localhost:8001/docs
make web     # http://localhost:4200
make agent   # registra el worker en LiveKit
```

Con la API y la web arriba, <http://localhost:4200> muestra el estado del
entorno: es la comprobación de que las piezas se hablan.

Requisitos, qué corre dónde y qué hacer cuando algo falla:
[docs/entorno-local.md](docs/entorno-local.md).

## Probar y verificar

```bash
make pruebas      # pruebas de los tres desplegables, el paquete común y la web
make verificar    # exactamente lo que corre el pipeline, en tu máquina
```

`make verificar` ejecuta formato, análisis estático, pruebas con cobertura,
compilación de la web y sus pruebas. Si pasa en local, el pull request no
debería fallar por análisis ni por pruebas. `make` sin argumentos lista todo lo
demás.

## Estructura

```
agilina/
├── shared/    Modelos de dominio y contrato worker ↔ API (Python)
├── api/       API en FastAPI: dominio, razonamiento al cierre, planificador
├── agent/     Worker de LiveKit Agents: todo lo que ocurre en la ceremonia
├── stt/       Servicio de transcripción con faster-whisper sobre GPU
├── web/       Aplicación web en Angular
├── infra/     Compose de Postgres y Keycloak, realm versionado
├── docs/      Documentación técnica y decisiones arquitectónicas
└── .github/   Pipeline de verificación y plantillas
```

Un solo repositorio con tres desplegables y un paquete común. El worker vive y
muere con la ceremonia, la API es un proceso de larga vida y la transcripción
necesita GPU: por eso son tres procesos y no uno. Comparten repositorio para
que el contrato entre ellos sea código compartido y no documentación que se
desactualiza.

## Stack

| Pieza | Tecnología |
| --- | --- |
| Aplicación web | Angular con `livekit-client` |
| API | Python con FastAPI |
| Worker del agente | Python con LiveKit Agents |
| Transporte de audio | LiveKit |
| Reconocimiento de voz | faster-whisper autohospedado sobre GPU |
| Razonamiento | Gemini Flash |
| Síntesis de voz | ElevenLabs |
| Persistencia | PostgreSQL con SQLAlchemy y Alembic |
| Identidad | Keycloak autohospedado |
| Trabajo en segundo plano | Planificador con almacén en la base de datos |
| Integraciones | Slack, Jira y Microsoft Graph |

La justificación de cada elección está en el documento de arquitectura. Todos
los proveedores externos quedan detrás de puertos intercambiables: cambiar de
transcripción, de modelo de lenguaje o de síntesis es sustituir un adaptador.

## Configuración

Todo se lee de variables de entorno. `.env.example` declara las claves
esperadas sin ningún valor real; `make env` lo copia a `.env`, que nunca se
versiona. Ninguna credencial vive en el repositorio: es parte del Definition of
Done del equipo, no el criterio de una sola historia.

## Cómo se trabaja

Ramas, commits, pull requests y code review: [CONTRIBUTING.md](CONTRIBUTING.md).
Configuración del repositorio y protección de `main`: [docs/github.md](docs/github.md).

Cada release se etiqueta al cerrarse: `v1.0` para la primera versión local
(Release 1), `v2.0` para la primera versión en la nube (Release 2) y `v3.0`
para la versión final validada (Release 3).

## Estado

Esqueleto del Sprint 0: los cuatro componentes arrancan, se hablan entre sí y
tienen pruebas, pero todavía no hay facilitación de ceremonias. Las capacidades
del producto llegan con las historias del backlog, sprint por sprint.
