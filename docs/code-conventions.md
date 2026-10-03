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
  `web/src/app/core/i18n/*.json` para la interfaz). Una prueba falla si una clave
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

## Errores

- El dominio y los casos de uso lanzan **excepciones de dominio tipadas**
  (`InvitationExpiredError`), con nombre que termina en `Error`. Nunca
  `Exception` pelada ni `except Exception` fuera de un borde del sistema (una
  frontera donde degradar es la política, como el planificador en el `lifespan`).
- Un único manejador en `presentation` traduce cada excepción a una respuesta
  HTTP y a una clave de i18n. El dominio no conoce códigos HTTP.
- Un error de un servicio externo se traduce en el adaptador a un error del
  puerto; los detalles del proveedor no suben a `application`.

## Tiempo, aleatoriedad y multi-tenant

- **Todo en UTC** (AD-20). El instante se obtiene de un puerto `Clock`, nunca de
  `datetime.now()` en el dominio: así la caducidad de siete días se prueba sin
  esperar. La zona horaria es asunto del navegador.
- Lo aleatorio y lo secreto (tokens) viene de un puerto (`TokenGenerator`) que
  usa `secrets`; el token en claro nunca se persiste, solo su hash.
- **El equipo es el tenant.** Todo repositorio y toda consulta con datos de
  equipo reciben el `team_id` como parámetro obligatorio: no puede olvidarse
  porque la firma lo pide. La autorización se evalúa contra el **rol interno**
  del integrante en ese equipo, nunca contra la etiqueta visible ni contra un
  claim del token sin contrastarlo con la membresía.

## Configuración, secretos y registros

- Toda la configuración sale de variables de entorno y su clave está en
  `.env.example`. Ningún valor real entra al repositorio.
- Los registros (*logs*) no llevan tokens, contraseñas ni correos completos.
- Un adaptador registra cada llamada a un sistema externo con su resultado.

## Pruebas

| Capa | Cómo se prueba |
| --- | --- |
| `domain` | Pruebas unitarias puras, sin base de datos ni red; se escriben antes que el código (TDD) |
| `application` | Con puertos falsos que cumplen el `Protocol` |
| `infrastructure` | De integración, contra Postgres y Keycloak reales en contenedores |
| `presentation` | Contra la aplicación con un cliente HTTP; verifican el contrato, no la lógica |

- La **meta de cobertura** es 90 % como mínimo en `domain` y `application`. Aún
  no se hace cumplir en la CI: se activa cuando existan esos paquetes.
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

- Componentes `standalone`, con `OnPush` y señales; prefijo `agl` en los
  selectores. *(ESLint.)*
- Estructura `core/` y `features/<contexto>/{domain,application,infrastructure,presentation}`.
  Presentación no importa infraestructura y el dominio no conoce Angular ni
  rxjs. *(ESLint.)*
- Los **puertos** son clases abstractas que sirven de token de inyección; el
  adaptador HTTP se enlaza en `app.config.ts`.
- Los componentes de presentación leen señales de un *facade* de `application`
  y no hacen peticiones HTTP.
- Ningún texto de usuario escrito en una plantilla: siempre una clave de i18n.
