# Convenciones de código

Cómo se escribe el código de Agilina. La organización de carpetas y capas está
en [estructura-del-proyecto.md](estructura-del-proyecto.md) y la decisión que
las respalda en [AD-21](adr/0021-organizar-el-codigo-en-contextos-y-capas.md);
las reglas de git, en [CONTRIBUTING.md](../CONTRIBUTING.md). El vocabulario del
dominio está en [glossary.md](glossary.md).

Cada regla dice si **la verifica una herramienta** o si depende del code
review. Lo que una herramienta hace cumplir no se discute en el review.

## Idioma

- **Inglés:** identificadores, nombres de archivos y carpetas, comentarios y
  *docstrings*, rutas HTTP, campos JSON, claves de i18n, variables de entorno y
  objetivos de `make`.
- **Español:** commits, pull requests, ADR y documentación de `docs/`.
- **Textos que ve el usuario:** nunca dentro del código; van en español e inglés
  mediante i18n (`shared/.../i18n.py` para lo que Agilina dice y
  `web/public/i18n/*.json` para la interfaz). Una prueba falla si una clave
  existe en un idioma y no en el otro.
- Los nombres de dominio salen del [glosario](glossary.md): si un concepto no
  está, se agrega ahí antes de usarlo en el código.

## Dominio (DDD)

- Un **agregado** tiene una raíz que protege sus invariantes: nada fuera de la
  raíz modifica el estado interno. Las reglas de negocio viven en métodos del
  agregado, no en los casos de uso ni en los routers.
- Un **repositorio por agregado**, con una interfaz en `domain` que habla en
  agregados (`add`, `get`, `save`), nunca en filas ni en consultas.
- Los **objetos de valor** son inmutables y se validan al construirse
  (`@dataclass(frozen=True)`): `Email`, `TokenHash`, `TeamRole`. Un valor
  inválido no puede existir.
- Los **eventos de dominio** se nombran en pasado (`InvitationAccepted`) y los
  produce el agregado; quien persiste los publica.
- El dominio **no importa** FastAPI, SQLAlchemy, Pydantic, `httpx` ni ninguna
  otra biblioteca de infraestructura. *(Lo verifica `import-linter`, también sobre
  el núcleo compartido `shared_kernel`.)*
- Los modelos ORM **no** son las entidades del dominio. Viven en
  `infrastructure` y se convierten con mapeadores.

## Capas y dependencias

*Lo verifica `import-linter` (Python) y ESLint (web).*

- `presentation` e `infrastructure` → `application` → `domain`. Nunca al revés.
- `presentation` no importa `infrastructure`. Si necesita algo, lo declara como
  dependencia y la raíz de composición se lo entrega.
- Un contexto no importa a otro: se hablan por los casos de uso o los eventos
  del otro.
- Solo la raíz de composición (`bootstrap/`, `main.py`, `app.config.ts`) conoce
  qué adaptador concreto atiende cada puerto.

## Persistencia

- Un repositorio **no filtra por estado calculado**: un estado que depende del tiempo
  (una invitación vencida) se *calcula* en el agregado (`state_at`); el repositorio solo
  guarda lo que el agregado ya decidió. Por eso `find_pending` devuelve lo *almacenado*
  como pendiente, que puede estar vencido: quien invita de nuevo debe llamar a
  `expire_if_due`, guardar y recién entonces insertar la nueva.
- **Una excepción a «el `team_id` va en toda firma»:** buscar una invitación por el hash de
  su token. El token (impredecible) es la credencial que identifica la invitación y, con
  ella, el equipo; es el único punto de entrada donde el tenant no se conoce de antemano.
  Todo lo demás exige el `team_id`.
- Cuando dos peticiones pueden disputarse un agregado (activar el mismo enlace dos veces),
  el repositorio lo bloquea con `SELECT … FOR UPDATE` al cargarlo: la segunda espera y
  encuentra el enlace ya usado. Hay una prueba de integración que falla si se quita el
  bloqueo.
- Los modelos ORM de un contexto **no declaran claves foráneas hacia otro contexto**: las
  define la migración y las hace cumplir la base de datos. Así un contexto no conoce las
  tablas de otro.
- Un repositorio escribe solo las columnas que el dominio conoce; lo demás (por ejemplo
  `team_member.slack_user_id`, de una historia posterior) queda como está.
- **Las migraciones se escriben a mano, en SQL.** El *autogenerate* de Alembic no sirve
  aquí: al probarlo contra el esquema real proponía decenas de operaciones, entre ellas
  borrar columnas que existen (`updated_at`, `slack_user_id`, los umbrales de ceremonia) y
  restricciones, índices parciales y claves entre contextos que el ORM no declara. Los
  modelos ORM son un subconjunto deliberado de las tablas. `make migration` crea una
  migración vacía para escribirla en SQL; el test de migraciones comprueba que cada columna
  del ORM exista en la base de datos con la misma nulabilidad.
- **Mientras el desarrollo sea local, las migraciones no se parchean: se reescriben.** Nadie más
  tiene datos que dependan de ellas, así que un cambio de esquema se hace en la migración
  inicial (hoy una por entorno: `tenant` y `platform`) y se construye todo de nuevo con
  `make clean` y `make up`. Desde el primer despliegue compartido, un cambio es una migración
  nueva y las anteriores ya no se tocan.

## Entre contextos

- Un contexto **declara como puerto** lo que necesita de otro (`TeamMembership`,
  `TeamContactsDirectory` en `identity`) y la **raíz de composición** lo implementa llamando
  al caso de uso del otro (`bootstrap/context_adapters.py`). Ningún contexto importa a otro;
  import-linter lo impide.
- Un manejador que **abre su propia transacción** (`CreateTeam`, `ActivateAccount`) recibe una
  fábrica de unidad de trabajo. Uno que existe para usarse **dentro** de la transacción de
  otro (`AddTeamMember`) recibe el repositorio y deja el commit al que lo llama.
- Un efecto en un sistema externo que no puede ir en la transacción (crear la cuenta en
  Keycloak) tiene su **compensación**: si el resto falla, se deshace, y el error original
  es el que se propaga (AD-24).
- Lo irreversible va al final y lo que puede fallar, antes: el correo de una invitación se
  envía antes del commit para que, si el servidor lo rechaza, no quede nada guardado.

## Comandos y consultas (CQRS)

- **Comando:** cambia estado. Cargar el agregado por su repositorio, ejecutar su
  comportamiento, persistir con la unidad de trabajo y publicar los eventos. Un
  comando no devuelve datos de lectura (a lo sumo el identificador que creó).
- **Consulta:** solo lee y no tiene efectos secundarios. Va directa a SQL y
  devuelve DTO; no pasa por agregados ni repositorios.
- Un caso de uso por clase. Su nombre es un verbo del dominio
  (`ActivateAccount`, `GetInvitationStatus`), no `Service` ni `Manager`.
- Los DTO de entrada y salida de un caso de uso son tipos simples de
  `application`: no son modelos de Pydantic ni del ORM.

## SOLID, como se ve en este proyecto

- **S.** Un manejador atiende un caso de uso; un adaptador habla con un solo
  sistema externo.
- **O.** Agregar un proveedor (SES en lugar de SMTP) es un adaptador nuevo, sin
  tocar los casos de uso.
- **L.** Los dobles de prueba cumplen exactamente el `Protocol` del puerto, y
  una prueba de contrato se corre contra el adaptador real y contra el falso.
- **I.** Los puertos son pequeños y propios de cada caso de uso: no hay un
  `KeycloakService` con veinte métodos, sino `IdentityProvider` con lo que
  `ActivateAccount` necesita.
- **D.** Los casos de uso dependen de `Protocol`s de `application`, no de
  clases concretas.

## Código limpio

- Nombres que dicen qué es o qué hace; sin abreviaturas que haya que descifrar.
- Funciones cortas, de un solo nivel de abstracción y con retornos tempranos
  antes que anidamiento. Sin banderas booleanas como parámetro: dos métodos con
  nombre propio.
- Un comentario explica el **porqué**, nunca lo que el código ya dice. Si hace
  falta explicar qué hace, el nombre está mal.
- Sin código muerto ni comentado, sin `TODO` sin historia (`TODO(HU-nn)`).
- Tipado completo en Python (`mypy --strict`, *lo verifica la CI*) y
  `strict` en TypeScript.
- Sin valores mágicos: una constante con nombre o un ajuste de configuración.
- **Una clase por archivo**, y el nombre del archivo es el de la clase: `InvalidEmailError` vive
  en `invalid_email_error.py` (Python, `snake_case`) o `invalid-email-error.ts` (TypeScript,
  `kebab-case`). Un comando y su manejador son dos clases, así que dos archivos
  (`activate_account.py` y `activate_account_handler.py`). Una constante o una función auxiliar va
  en el archivo de la única clase que la usa; si nadie la usa, tiene el suyo (`catalog_of.py`).
  Los tipos y las interfaces de TypeScript viajan con la clase a la que describen.
  - Cuando un tema reúne varias clases (los errores de un dominio, los objetos de valor, los
    esquemas HTTP, los modelos ORM), es un **paquete** con el nombre del tema (`errors/`,
    `value_objects/`, `schemas/`, `orm_models/`) cuyo `__init__.py` reexporta sus clases con
    `__all__`: quien importa escribe `from agilina_api.identity.domain.errors import
    InvalidEmailError`, no la ruta del archivo. La docstring del módulo original pasa al
    `__init__.py`.
  - Una prueba (`tests/api/unit/test_one_class_per_file.py`) falla si un archivo de `api/src` o de
    `shared/src` declara más de una clase. Los dobles y *builders* de `tests/` no se rigen por
    esta regla.

## Errores

- El dominio y los casos de uso lanzan **excepciones de dominio tipadas**
  (`InvitationExpiredError`), con nombre que termina en `Error`. Nunca
  `Exception` pelada ni `except Exception` fuera de un borde del sistema (una
  frontera donde degradar es la política, como el planificador en el `lifespan`).
- Los manejadores de `presentation` traducen cada excepción a una respuesta HTTP con el
  formato único de error y un `code` estable que la web traduce ([AD-30](adr/0030-un-solo-formato-de-error-http-y-un-catalogo-de-la-api.md)).
  El dominio no conoce códigos HTTP. Cada endpoint se documenta en [api.md](api.md).
- Un error de un servicio externo se traduce en el adaptador a un error del
  puerto; los detalles del proveedor no suben a `application`.

## Tiempo, aleatoriedad y multi-tenant

- **Todo en UTC** (AD-20). El instante se obtiene de un puerto `Clock`, nunca de
  `datetime.now()` en el dominio: así la caducidad de siete días se prueba sin
  esperar. La zona horaria es asunto del navegador.
- Lo aleatorio y lo secreto (tokens) viene de un puerto (`TokenGenerator`) que
  usa `secrets`; el token en claro nunca se persiste, solo su hash.
- **Dos niveles de aislamiento.** El **tenant** es la organización, con su base de datos y su
  realm ([AD-29](adr/0029-un-tenant-es-una-organizacion-con-su-base-y-su-realm.md)): se elige en
  el borde, una vez por petición, y nada de lo que hay detrás lo repite ni lo conoce. Dentro de
  él, el **equipo** aísla los datos: todo repositorio y toda consulta con datos de equipo reciben
  el `team_id` como parámetro obligatorio, y no puede olvidarse porque la firma lo pide. La autorización se evalúa contra el **rol interno**
  del integrante en ese equipo, nunca contra la etiqueta visible ni contra un
  claim del token sin contrastarlo con la membresía.

## Configuración, secretos y registros

- Toda la configuración sale de variables de entorno y su clave está en
  `.env.example`. Ningún valor real entra al repositorio.
- Los registros (*logs*) no llevan tokens, contraseñas ni correos completos.
- Un adaptador registra cada llamada a un sistema externo con su resultado.

## Pruebas

Dónde van, cómo se arman los datos (*Data Builders*) y qué se prueba en cada capa:
[testing.md](testing.md), con su decisión en
[AD-25](adr/0025-organizar-las-pruebas-con-arbol-espejo-builders-y-cobertura-total.md).

- Las pruebas están en `tests/` (raíz), con un árbol `unit/` y otro `integration/`, cada
  uno con la estructura de `src/`.
- Cada capa tiene sus pruebas: `domain` (puras), `application` (con puertos falsos que
  cumplen el `Protocol`), `presentation` (cliente HTTP), `infrastructure` (PostgreSQL y
  Keycloak reales) y `bootstrap` (cableado y comandos del operador).
- La **cobertura de la API y del contrato compartido es del 100 %** y la CI falla por
  debajo (`make coverage`).
- Una prueba describe un comportamiento, no un método: `test_an_expired_link_is_rejected`.
- Una prueba no depende de otra ni del orden; el reloj y la aleatoriedad se
  inyectan.
- Todo error corregido deja una prueba que lo habría detectado.

## Python

- `ruff` decide formato y reglas; `mypy --strict` el tipado; `pytest` con
  `asyncio_mode = auto`. Todo en el `pyproject.toml` de la raíz. *(`make verify`.)*
- Los paquetes se llaman `agilina_<pieza>`; las importaciones son absolutas.
- Los modelos de contrato entre desplegables viven en `agilina_shared` y
  prohíben campos desconocidos (`extra="forbid"`).

## Angular y TypeScript

La guía completa de la web está en [web/README.md](../web/README.md) y sus
decisiones en [AD-26](adr/0026-organizar-y-equipar-la-aplicacion-web.md). Lo
esencial:

- Angular 22 zoneless; componentes *standalone* y `OnPush` (los valores por
  defecto), signals para el estado y `inject()` para las dependencias; prefijo
  `agl` en los selectores. *(ESLint.)*
- Prettier decide el formato y ESLint (*type-checked*) el resto. *(`make verify`.)*
- Estructura `core/`, `layout/`, `shared/` y
  `features/<contexto>/{domain,application,infrastructure,presentation}`, con
  alias `@core/*`, `@shared/*`, `@layout/*` y `@features/*`. Las capas apuntan
  hacia adentro, una funcionalidad no importa a otra y el dominio no conoce
  Angular ni rxjs. *(ESLint, sobre el archivo resuelto.)*
- Los **puertos** son clases abstractas que sirven de token de inyección; los
  adaptadores se enlazan en `app.config.ts`.
- Las páginas leen signals de una *facade* de `application` y no hacen
  peticiones HTTP.
- Ningún texto de usuario escrito en una plantilla: siempre una clave de
  Transloco.
- Los estilos son clases de **Tailwind CSS** en la plantilla ([AD-27](adr/0027-dar-estilo-a-la-web-con-tailwind-css.md)),
  con colores solo de los tokens `--agl-*` (`bg-surface`, `text-muted`…); lo que se repite es una
  pieza de `shared/ui`, no un grupo de clases copiado.
- Los errores se registran con el puerto `Logger`; `console.*` está prohibido
  fuera de su adaptador. *(ESLint.)*
- La configuración llega en `config.json`, generado desde variables de entorno
  al arrancar el contenedor: ninguna URL en el código.
