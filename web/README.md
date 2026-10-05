# Agilina · Frontend (Angular)

Cliente web de Agilina, un Scrum Master virtual que facilita la Daily por voz. Es
uno de los componentes del monorepo, junto con la API (FastAPI), el worker del
agente (LiveKit Agents) y el servicio de transcripción (faster-whisper).

Esta guía es la fuente de verdad de cómo se construye la web. Lo que es común a
todo el repositorio (git, Definition of Done, glosario) vive en
[CONTRIBUTING.md](../CONTRIBUTING.md), [docs/code-conventions.md](../docs/code-conventions.md)
y [docs/glossary.md](../docs/glossary.md). El porqué de las decisiones de esta
guía está en [AD-26](../docs/adr/0026-organizar-y-equipar-la-aplicacion-web.md).

## Stack

| Pieza | Elección |
| --- | --- |
| Framework | Angular 22, **zoneless** y con **`OnPush` por defecto**. El estado se maneja con signals |
| Lenguaje | TypeScript 6 en modo estricto, con `noUncheckedIndexedAccess` y `exactOptionalPropertyTypes` |
| Sala de audio | `livekit-client`. No se usan los componentes prearmados de LiveKit, que son solo para React |
| Identidad | Keycloak (OIDC) con `keycloak-js`. La API emite el token de LiveKit |
| Textos | [Transloco](https://jsverse.gitbook.io/transloco) (`@jsverse/transloco`), español e inglés |
| Formularios | Reactive Forms tipados (`@angular/forms`) |
| Análisis estático | ESLint con `angular-eslint`, `typescript-eslint` (reglas *type-checked*) e `import-x` |
| Formato | Prettier |
| Pruebas | Jasmine con Karma sobre Chromium sin interfaz |
| Ejecución | Todo corre dockerizado: en desarrollo `ng serve`, en producción nginx sin privilegios |

## Cómo se corre

Solo hacen falta Docker y `make`, desde la raíz del repositorio:

```bash
make up          # levanta todo; la web queda en http://localhost:4200
make test-web    # pruebas de la web en Chromium sin interfaz
make lint        # ESLint (y ruff para Python)
make format      # Prettier sobre la web (y ruff format sobre Python)
make verify      # exactamente lo que corre la CI
make lock        # tras cambiar package.json: regenera package-lock.json
```

Dentro de `web/`, los scripts de `package.json` son los mismos que usa la CI:
`lint`, `format`, `format:check`, `build`, `test:ci`.

## Reglas de arquitectura

- **El cliente no contiene reglas de autorización.** Solo oculta lo que la API
  ya protege: ocultar un elemento de la interfaz no cuenta como control de acceso.
- **Los controles de la ceremonia** (iniciar daily, terminar turno, cerrar ronda)
  se publican por el canal de datos de la sala de LiveKit, dirigidos al agente.
  No pasan por la API.
- **El cierre del turno es manual:** el participante pulsa «terminar turno». No
  se detecta por pausas.
- **La sala no muestra la transcripción en vivo.** Muestra los participantes
  conectados, quién está hablando, el turno en curso y el estado de Agilina.
- **Fechas en UTC.** Llegan y se envían en UTC y se muestran en la zona horaria
  del navegador. No existe zona horaria por equipo.
- **Configuración por variables de entorno.** Nunca se escriben credenciales,
  llaves ni URLs en el código (ver [Configuración](#configuración)).
- **La pestaña de configuración** solo se muestra a los roles Admin y SM. En el
  código ambos son el mismo rol interno `admin` (SM es su etiqueta visible en
  modo soporte, ver el [glosario](../docs/glossary.md)): la interfaz decide con
  el rol interno, nunca con la etiqueta.

## Estructura de carpetas

Primero por funcionalidad y después por capa, igual que la API
([AD-21](../docs/adr/0021-organizar-el-codigo-en-contextos-y-capas.md)):

```
web/
├── public/
│   └── i18n/{es,en}.json        Catálogos de textos
├── runtime-config.template.json  Plantilla de config.json (variables de entorno)
├── scripts/                      render-runtime-config.mjs (config.json en desarrollo)
└── src/
    ├── main.ts                   Carga config.json y arranca la aplicación
    ├── styles.scss               Tokens de diseño (--agl-*) y estilos globales
    ├── testing/                  Utilidades de prueba compartidas (@testing/*)
    └── app/
        ├── app.config.ts         Raíz de composición: enlaza puertos con adaptadores
        ├── app.routes.ts         Mapa de pantallas, todas con carga diferida
        ├── app.ts                Componente raíz: layout + router-outlet
        ├── core/                 Singletons de toda la aplicación (@core/*)
        │   ├── config/           RuntimeConfig, su validación y su carga
        │   ├── http/             Interceptores
        │   ├── i18n/             Transloco, idiomas y manejo de claves faltantes
        │   ├── logging/          Puerto Logger, adaptador de consola, ErrorHandler
        │   └── auth/             Keycloak (llega con la historia de autenticación)
        ├── layout/               Marco de la aplicación: cabecera, navegación (@layout/*)
        ├── shared/               Reutilizable y sin estado (@shared/*)
        │   ├── ui/               Componentes de presentación genéricos
        │   ├── pipes/
        │   └── utils/            Funciones puras
        └── features/             Una carpeta por contexto (@features/*)
            └── <contexto>/
                ├── domain/
                ├── application/
                ├── infrastructure/
                └── presentation/
```

Una carpeta se crea cuando llega su primer archivo: no se dejan carpetas vacías
ni código a la espera de usarse.

### Funcionalidades

Los nombres salen de los contextos de la API y del glosario, para que un
concepto se llame igual en todo el sistema:

| Funcionalidad | Qué contiene | Estado |
| --- | --- | --- |
| `status` | Estado del entorno: prueba que la web habla con la API | Existe |
| `identity` | Activación de la cuenta desde la invitación, inicio y cierre de sesión | Llega con HU-02/03/04 |
| `teams` | Equipo, integrantes y pestaña de configuración (solo `admin`) | Existe: selector mínimo, creación y dashboard placeholder (HU-05). El resto llega con sus historias |
| `ceremonies` | La sala de la Daily: LiveKit, turnos y controles hacia el agente | Llega con las historias de la ceremonia |

### Capas dentro de una funcionalidad

| Capa | Qué contiene | Puede importar |
| --- | --- | --- |
| `domain` | Modelos, objetos de valor y reglas puras (por ejemplo, de quién es el turno) | Solo su propio `domain`. Sin Angular, rxjs ni librerías |
| `application` | Puertos (clases abstractas) y *facades* con signals: el estado de la pantalla | `domain`, `@core/*`, `@shared/*` |
| `infrastructure` | Adaptadores: HTTP hacia la API, LiveKit, Keycloak. Mapean DTO ↔ dominio | `application`, `domain`, `@core/*` |
| `presentation` | Páginas y componentes | `application`, `domain`, `@core/*`, `@shared/*` |

`presentation` e `infrastructure` no se conocen: se encuentran solo en
`app.config.ts`, que decide qué adaptador atiende cada puerto. Cambiar de
proveedor es escribir un adaptador y cambiar una línea ahí.

### Fronteras que verifica ESLint

Romper una de estas reglas hace fallar `make lint`; cambiarla exige tocar
`eslint.config.js`, y eso se ve en el code review.

| Regla | Herramienta |
| --- | --- |
| Las capas apuntan hacia adentro; `presentation` no importa `infrastructure` | `import-x/no-restricted-paths` |
| Una funcionalidad no importa a otra (se hablan por la API o por el router) | `import-x/no-restricted-paths` |
| `core` no conoce `features` ni `layout`; `shared` no conoce `core`, `layout` ni `features`; `layout` no conoce `features` | `import-x/no-restricted-paths` |
| El dominio no importa Angular, rxjs ni ninguna librería | `no-restricted-imports` |
| `HttpClient`, `livekit-client` y `keycloak-js` solo en adaptadores (`infrastructure`, `core`) | `no-restricted-imports` |
| Nada escribe en la consola salvo el adaptador del `Logger` y `main.ts` | `no-console` |
| Sin ciclos de importación ni exportaciones por defecto | `import-x/no-cycle`, `import-x/no-default-export` |
| Ningún componente vuelve a `ChangeDetectionStrategy.Eager` | `no-restricted-syntax` |

## Convenciones de nombres

Todo el código va en inglés: identificadores, comentarios, nombres de archivo y
claves de i18n. Los textos que ve el usuario van en los catálogos, en español y
en inglés.

| Qué | Archivo | Clase o símbolo |
| --- | --- | --- |
| Página enrutada | `team-settings-page.ts` (+ `.html`, `.scss`) | `TeamSettingsPage`, selector `agl-team-settings-page` |
| Componente | `participant-tile.ts` | `ParticipantTile`, selector `agl-participant-tile` |
| Puerto | `room.port.ts` | `RoomPort` (clase abstracta) |
| *Facade* | `room.facade.ts` | `RoomFacade` |
| Adaptador HTTP | `http-teams.api.ts` | `HttpTeamsApi` |
| Otro adaptador | `livekit-room.adapter.ts` | `LiveKitRoomAdapter` |
| Modelo de dominio | `turn.ts` | `Turn` |
| Interceptor, *guard*, *pipe* | `auth.interceptor.ts`, `admin.guard.ts`, `local-date.pipe.ts` | `authInterceptor`, `adminGuard` (funciones), `LocalDatePipe` |
| Validador de formulario | `team-name.validator.ts` | `teamNameValidator` (función) |
| Proveedores de un módulo de `core` | `provide-logging.ts` | `provideLogging()` |
| Prueba | junto al archivo, `*.spec.ts` | — |

- Archivos en `kebab-case`; clases y tipos en `PascalCase`; el resto en
  `camelCase`; constantes globales en `UPPER_CASE`. *(ESLint.)*
- Los componentes no llevan sufijo `Component` (guía de estilo de Angular 20+).
- Selectores con prefijo `agl`. *(ESLint.)*
- Dentro de una misma funcionalidad, importaciones relativas; entre zonas,
  alias: `@core/*`, `@shared/*`, `@layout/*`, `@features/*` (este último solo
  en `app.config.ts` y `app.routes.ts`) y `@testing/*` en pruebas.
- Importaciones ordenadas por grupos (Angular y librerías, alias, relativas)
  y alfabéticamente. *(ESLint, se corrige con `--fix`.)*

## Componentes

- *Standalone* (el valor por defecto) y `OnPush` (el valor por defecto en
  Angular 22). No se escribe `standalone: true` ni `changeDetection`.
- Dependencias con `inject()`, nunca por constructor. *(ESLint.)*
- Entradas y salidas con `input()`, `input.required()`, `output()` y
  `model()`; consultas con `viewChild()` y `contentChild()`. *(ESLint.)*
- Plantilla y estilos en archivos aparte (`templateUrl`, `styleUrl`); control
  de flujo nativo (`@if`, `@for`, `@switch`), con `track` en todo `@for`.
- Lo que solo usa la plantilla es `protected`; lo que nadie fuera usa,
  `private`. Nunca `public` explícito. *(ESLint.)*
- Una página lee signals de su *facade* y le delega las acciones: no hace
  peticiones, no se suscribe a observables ni contiene reglas de negocio.
- Los componentes de `shared/ui` son de presentación pura: reciben entradas y
  emiten salidas, sin *facades* ni servicios.
- Nada de lógica en el constructor más allá de inicializar campos.

## Estado y reactividad

- **Signals para el estado,** rxjs solo en los bordes (HTTP, eventos de
  LiveKit). Un adaptador puede devolver `Observable`; la *facade* lo convierte
  en signals.
- Las lecturas de datos usan `rxResource` (o `resource`), que ya expone
  `isLoading`, `status`, `error` y `reload()`. Ver `StatusFacade`.
- Una *facade* expone signals de solo lectura (`computed` o `.asReadonly()`):
  la presentación no escribe el estado, llama métodos.
- Una *facade* se provee en la página (`providers: [RoomFacade]`) para que viva
  y muera con ella. Solo va a `providedIn: 'root'` si su estado debe sobrevivir
  a la navegación (por ejemplo, la sesión).
- Si un componente o una *facade* tiene que suscribirse a mano, lo hace con
  `takeUntilDestroyed()`. *(ESLint verifica que se use en un contexto válido.)*
- `effect()` solo para sincronizar con el mundo exterior (DOM, LiveKit,
  `localStorage`), nunca para derivar estado: para eso está `computed()`.

## Formularios

- **Reactive Forms tipados** (`ReactiveFormsModule`): un `FormGroup` con sus
  `FormControl` creados con `nonNullable: true`, como campos `protected` de la
  página. Se envía con `(ngSubmit)` sobre `[formGroup]`.
- **La regla vive en `domain`** como función pura (por ejemplo,
  `teamNameProblem` en `features/teams/domain/team-name.ts`), con su prueba sin
  `TestBed`. El validador es una función de `presentation`
  (`team-name.validator.ts`) que solo delega en esa regla: no repite la regla.
- **La validación del cliente es comodidad; la autoridad es la API.** La API
  aplica la misma regla y responde con un `code` (`invalid_team_name`). Hoy la
  pantalla muestra un error genérico traducido ante cualquier fallo; traducir
  cada `code` llega cuando una historia lo necesite.
- El botón de enviar queda deshabilitado mientras el formulario sea inválido o
  se esté guardando. Los mensajes de validación se muestran cuando el usuario ya
  escribió en el campo o salió de él.
- Todo control tiene su `<label for>`, y el mensaje de error se asocia con
  `aria-describedby` y `aria-invalid`.
- El envío lo hace la *facade* (`saving`, `failed` y un método que devuelve una
  `Promise`); la página solo decide adónde navegar con el resultado.

## Comunicación con la API

- Solo los adaptadores de `infrastructure` usan `HttpClient`. *(ESLint.)*
- La URL base sale de `RUNTIME_CONFIG.apiUrl`; nunca se escribe una URL.
- El adaptador define la forma del JSON de la API (`HealthResponse`) y la mapea
  al modelo de dominio: el contrato no se filtra a `application` ni a la
  pantalla. Los campos del JSON conservan el nombre de la API.
- Un cambio que rompe el contrato con la API se marca con `BREAKING CHANGE`.

## Sala de LiveKit

- `livekit-client` solo se importa en el adaptador de la sala, dentro de
  `features/ceremonies/infrastructure`, detrás de un puerto que habla el
  lenguaje del dominio (participantes, turno, estado de Agilina).
- El token de la sala lo pide el adaptador HTTP a la API; nunca se genera en
  el cliente.
- Los controles de la ceremonia viajan como mensajes por el canal de datos de
  la sala, dirigidos al agente. Su formato es un contrato con el worker y se
  documenta en [docs/contrato-worker-api.md](../docs/contrato-worker-api.md)
  cuando se defina.
- La pantalla no muestra transcripción en vivo.

## Autenticación y autorización

- La sesión la resuelve Keycloak (OIDC); la integración vive en `core/auth`
  y se construye con su historia.
- Las rutas restringidas usan un *guard* y los elementos restringidos se
  ocultan según el rol interno, pero **la autorización es de la API**: un
  *guard* es comodidad para el usuario, no seguridad.

## Fechas y zonas horarias

- La API envía y recibe instantes en ISO 8601 con zona UTC (`...Z`).
- Al enviar, `date.toISOString()`. Al mostrar, `Intl.DateTimeFormat` con el
  idioma activo como *locale* y sin `timeZone`, de modo que usa la del
  navegador. El formateo vive en una función pura de `shared/utils` (o en un
  *pipe* de `shared/pipes`) cuando lo necesite la primera pantalla.
- No se guarda ni se calcula con zonas horarias por equipo: no existen.

## Textos e i18n

- Ningún texto de usuario en el código ni en las plantillas: siempre una clave
  de los catálogos `public/i18n/es.json` y `en.json`.
- Claves en inglés, anidadas por funcionalidad y en `snake_case`:
  `status.error_hint`, `teams.settings.title`. Lo común a toda la aplicación,
  bajo `app`.
- En plantillas, la directiva estructural con prefijo, una vez por plantilla:

  ```html
  <section *transloco="let t; prefix: 'status'">
    <h1>{{ t('title') }}</h1>
  </section>
  ```

- En código (raro: casi todo texto vive en plantillas), `translateSignal()`.
- El idioma inicial es el del navegador; el definitivo es un atributo del
  equipo y llega de la API. `<html lang>` se actualiza solo.
- Una clave faltante se registra como advertencia y se muestra como la clave
  misma: un error visible, no un hueco en blanco.
- Una prueba falla si una clave existe en un idioma y no en el otro, o si un
  texto está vacío.

## Errores y registro

El estándar es un **puerto `Logger`** (`@core/logging/logger`) con entradas
estructuradas. Hoy lo atiende `ConsoleLogger`; enviar los registros a otro
destino es un adaptador nuevo en `provide-logging.ts`, sin tocar a quien
registra.

- **Forma de una entrada:** `level`, `message`, `timestamp` (ISO 8601 en UTC),
  `context` (objeto con claves en `camelCase`) y `error` cuando lo hay.
- **Niveles:** `debug` (diagnóstico), `info` (hitos: entrar a la sala), `warn`
  (algo anómalo que se recupera: una clave faltante, un reintento) y `error`
  (algo falló). El mínimo sale de `AGILINA_LOG_LEVEL`.
- **Mensajes** en inglés, cortos y estables, para poder buscarlos: `'HTTP
  request failed'`, no frases con datos interpolados. Los datos van en
  `context`.
- **Nunca** se registran tokens, contraseñas, correos completos, cuerpos de
  petición ni audio. El interceptor registra método, URL sin *query* y estado.
- **Un error se registra una vez, donde se maneja:**
  - los errores HTTP, en `httpErrorLoggingInterceptor`;
  - los no manejados, en `GlobalErrorHandler` (incluye los del `window`);
  - los demás (LiveKit, Keycloak), en el adaptador que los recibe.
- La *facade* convierte el error en estado de pantalla (`failed`) y la
  pantalla muestra un mensaje traducido; nunca se traga un error en silencio
  ni se muestra el mensaje técnico al usuario.
- `console.*` está prohibido fuera del adaptador. *(ESLint.)*

## Configuración

Lo que cambia entre entornos se lee de **variables de entorno en tiempo de
ejecución**: una sola imagen sirve para todos los entornos y no hay URLs
compiladas en el bundle.

```
variables de entorno ─▶ runtime-config.template.json ─▶ /config.json ─▶ main.ts ─▶ RUNTIME_CONFIG
```

- En desarrollo, `scripts/render-runtime-config.mjs` la genera antes de
  `ng serve` en `runtime/` (ignorada por git). En producción, nginx la genera
  con `envsubst` al arrancar el contenedor.
- `main.ts` la descarga y la valida (`parseRuntimeConfig`) **antes** de
  arrancar Angular, de modo que cualquier proveedor la lee de forma síncrona
  con `inject(RUNTIME_CONFIG)`. Una variable faltante impide arrancar, con un
  mensaje que dice cuál.
- `config.json` es público por naturaleza: **nunca lleva secretos.**

Variables que lee la web: `AGILINA_API_PUBLIC_URL`, `AGILINA_KEYCLOAK_URL`,
`AGILINA_KEYCLOAK_REALM`, `AGILINA_KEYCLOAK_WEB_CLIENT` y `AGILINA_LOG_LEVEL`.

Para agregar una: declárala en `.env.example`, pásala al servicio `web` en
`infra/docker-compose.yml`, agrégala a `runtime-config.template.json`, a
`RuntimeConfig` y a su validación (con prueba), y a `TEST_RUNTIME_CONFIG`.

## Estilos

- Los colores, espacios y tipografía son tokens `--agl-*` en `styles.scss`. Un
  componente usa los tokens, no valores sueltos.
- Cada componente con su `.scss` encapsulado; nada de estilos en línea.
  *(ESLint.)*
- Presupuesto de 4 kB por hoja de estilos de componente (falla a los 8 kB).

## Accesibilidad

- Las reglas de accesibilidad de `angular-eslint` están activas: texto
  alternativo, etiquetas asociadas a sus controles, eventos de teclado junto a
  los de ratón y `type` en todo botón. *(ESLint.)*
- HTML semántico primero (`button`, `nav`, `main`, `dl`) y ARIA solo cuando no
  alcanza. En la sala, quién habla y el turno en curso se anuncian también en
  una región `aria-live`, no solo con color.

## Pruebas

| Qué | Cómo |
| --- | --- |
| `domain` y funciones puras | Pruebas unitarias sin `TestBed` |
| *facades* | Con el puerto falso (una clase que extiende el puerto), sin HTTP |
| Adaptadores HTTP | `provideHttpClientTesting()` y `HttpTestingController`: verifican URL, método y mapeo |
| Páginas y componentes | `TestBed` con el puerto falso y los catálogos reales (`provideTestI18n()`); verifican lo que ve el usuario |
| `core` | Cada pieza con sus dobles: `provideFakeLogger()`, `provideTestRuntimeConfig()` |

- Una prueba describe un comportamiento: `'warns when the API does not respond
  and retries on demand'`.
- Se afirma sobre el texto en español: si una clave se renombra o falta, la
  prueba falla.
- Sin zone.js: se espera con `await fixture.whenStable()`. Si una petición queda
  pendiente a propósito, `fixture.detectChanges()`.
- Las utilidades comunes viven en `src/testing` y se importan con `@testing/*`.
- Todo error corregido deja una prueba que lo habría detectado.

## Calidad (Definition of Done)

- Cero errores de análisis estático y ninguna advertencia nueva
  (`ng lint --max-warnings=0`).
- La lógica nueva lleva pruebas automatizadas, y el pipeline debe quedar en
  verde.
- Todo texto dirigido al usuario existe en español y en inglés.
- Los errores se manejan y se registran; no se tragan en silencio.
- No se revisa formato ni estilo en el Code Review: de eso se encargan Prettier
  y ESLint.

## Git

- GitHub Flow: `main` está protegida y todo entra por Pull Request.
- Las ramas se nombran `tipo/HU-nn-descripcion-corta`, en minúsculas y con
  guiones. Tipos: `feat`, `fix`, `chore`, `docs`, `spike`.
- Commits con Conventional Commits, en el formato `tipo(web): descripcion`, en
  español, en imperativo y en minúscula.
  - Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`,
    `ci`.
  - El cuerpo es opcional y explica el porqué, no el qué.
  - Todo commit termina con `Refs: HU-nn`.
  - Si se rompe un contrato con la API, se marca con `BREAKING CHANGE` en el pie.
- Cada commit tiene un solo autor. No se agrega `Co-Authored-By` ni líneas de
  atribución a Claude o a la sesión.

## Cómo agregar algo

**Una pantalla en una funcionalidad existente**

1. Si hay una regla nueva, va en `domain`, con su prueba sin `TestBed`.
2. Si necesita datos nuevos, declara el método en el puerto de `application` e
   impleméntalo en el adaptador de `infrastructure`, con su prueba.
3. Escribe o amplía la *facade* con signals de solo lectura.
4. Crea la página en `presentation`, con sus textos en los dos catálogos.
5. Agrega la ruta con `loadComponent` en `app.routes.ts`.
6. `make verify` en verde.

**Una funcionalidad nueva**

1. Crea `features/<contexto>/` con solo las capas que necesite. El nombre sale
   del glosario.
2. Enlaza sus puertos con sus adaptadores en `app.config.ts`.
3. Agrega su grupo de claves a los catálogos.
4. No hay que tocar `eslint.config.js`: las reglas de aislamiento se generan
   para cada carpeta de `features/`.

## Por decidir

Estos puntos no están decididos; se preguntan antes de decidir:

- Destino remoto de los registros (endpoint de la API, Sentry/GlitchTip u
  OpenTelemetry). Hoy solo consola.
- Librería de integración con Keycloak (`keycloak-angular` o `keycloak-js`
  directo) y cómo se renueva el token.
- Migrar las pruebas de Karma a Vitest (el valor por defecto desde Angular 21;
  Karma está archivado).
- Librería de componentes o sistema de diseño para `shared/ui`.
- Herramienta de pruebas de punta a punta en el navegador (por ejemplo,
  Playwright en su propio contenedor). Hoy los flujos se cubren con la
  integración HTTP de la API contra PostgreSQL y con pruebas de componentes con
  el Router real. Se decide cuando exista el inicio de sesión (HU-03).
