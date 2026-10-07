## Para agentes que trabajan en api/

Esta carpeta es la API (FastAPI): el código vive en `src/agilina_api/`, las migraciones en
`migrations/` y las pruebas en [`tests/api/`](../tests/CLAUDE.md), fuera de aquí.

- Las guías mandan, en este orden: [code-conventions.md](../docs/code-conventions.md),
  [estructura-del-proyecto.md](../docs/estructura-del-proyecto.md) y los ADR
  ([AD-21](../docs/adr/0021-organizar-el-codigo-en-contextos-y-capas.md) a
  [AD-25](../docs/adr/0025-organizar-las-pruebas-con-arbol-espejo-builders-y-cobertura-total.md)).
  Si algo no está decidido ahí, **pregunta antes de decidir**: no se inventan librerías,
  capas ni convenciones. Una decisión que cambia la forma del sistema se registra como ADR.
- Código, comentarios, nombres de archivo y mensajes de error en inglés. Commits, pull
  requests, documentación y ADR en español.
- Todo corre en contenedores; no se instala Python, uv ni nada en la máquina. Usa `make`:
  `lint`, `format`, `typecheck`, `arch`, `test-python`, `test-integration`, `coverage` y
  `verify`. Antes de dar algo por terminado: `make verify` en verde.
- Commits: un solo autor, sin `Co-Authored-By` ni líneas de atribución. Nada de commits ni
  push sin autorización explícita de quien lo pide, cada vez. Una rama por historia
  (`tipo/HU-nn-descripcion`).

## Dónde va cada cosa

```
src/agilina_api/
├── bootstrap/        Raíz de composición: aquí, y solo aquí, se elige qué adaptador atiende cada puerto
├── shared_kernel/    Entity, AggregateRoot, DomainEvent, DomainError
├── shared/           Lo común a los contextos, por capas (puertos Clock, Mailer, UnitOfWork…)
└── <contexto>/       identity, teams, ceremonies
    ├── domain/         Agregados, objetos de valor, eventos, errores, repositorios (interfaces)
    ├── application/    Comandos y consultas, puertos de salida, DTO
    ├── presentation/   Routers HTTP, esquemas, presentadores, dependencias
    └── infrastructure/ Persistencia, Keycloak, correo, mapeadores
```

Las capas apuntan hacia adentro: `presentation` e `infrastructure` → `application` →
`domain`. `make arch` (import-linter) lo verifica y falla si se rompe.

## Reglas de arquitectura

- **El dominio es Python puro:** sin FastAPI, SQLAlchemy, Pydantic ni httpx. Los invariantes
  viven en los agregados y se prueban sin servidores.
- **Un contexto no importa a otro.** Se hablan por puertos que el contexto que los necesita
  declara en su `application` y que `bootstrap/` implementa (`TeamsBackedMembership`,
  `TeamsBackedContacts`). Los contextos nunca se conocen entre sí.
- **El ORM no es el dominio.** Los modelos SQLAlchemy viven en `infrastructure` y se
  convierten con mapeadores; el dominio no sabe que existe una base de datos.
- **CQRS pragmático:** una sola base de datos, sin *event sourcing* ni bus. Los comandos pasan
  por el agregado y el repositorio; las consultas de lectura usan SQL directo y devuelven
  DTO.
- **Una unidad de trabajo por caso de uso.** El caso de uso abre la transacción y hace el
  `commit`; un manejador que se usa dentro de la transacción de otro (`AddTeamMember`) no
  hace `commit`.
- **Los casos de uso no conocen HTTP ni SQL.** Reciben comandos y devuelven DTO; los errores
  de negocio son `DomainError` y es `presentation` quien los convierte en estado HTTP y
  código estable.
- **Tiempo y azar se inyectan:** el instante sale del puerto `Clock` (siempre en UTC) y los
  identificadores se generan en el caso de uso, nunca dentro del dominio.
- **Multi-tenant:** el equipo es el tenant. Toda consulta de datos de un equipo filtra por él.
- **La API hace la autorización.** La interfaz solo oculta lo que la API ya protege.

## Seguridad

- Ninguna credencial, token ni secreto en el código ni en la configuración versionada: todo
  sale de variables de entorno (`AGILINA_*`, declaradas en `.env.example`).
- Un token de invitación se guarda **solo como hash SHA-256**; viaja en el cuerpo de la
  petición, nunca en la URL de la API, y ninguna respuesta lo repite.
- Nunca se registran tokens, contraseñas ni correos completos (un adaptador usa
  `mask_email`). Un adaptador registra cada llamada a un sistema externo con su resultado, y
  un mensaje de error de un sistema externo no se devuelve al cliente.
- Las respuestas de autenticación llevan `Cache-Control: no-store`.
- **Toda ruta nueva exige una sesión.** Declara `Depends(current_user_id)` (o
  `current_team_member` si es de un equipo): la API valida el token de Keycloak (firma, emisor,
  audiencia, vigencia) antes de confiar en él ([AD-28](../docs/adr/0028-iniciar-sesion-con-keycloak.md)).
  Una ruta pública es una excepción: se agrega a `PUBLIC` en
  `tests/api/unit/bootstrap/test_authentication.py`, con su razón; si no, esa prueba falla.
  Nunca se lee un rol ni un equipo del token: se consulta lo guardado.
- Los errores de la API tienen la forma `{code, detail, reasons?}`, con `code` estable: el
  cliente decide por el código, no por el texto.

## Migraciones

- Se escriben **a mano, en SQL**, en `migrations/versions/`. El *autogenerate* de Alembic
  propone borrar columnas reales y no se usa. `make migration m="descripcion"` crea una
  revisión vacía; `make migrate` aplica las pendientes.
- La prueba de migraciones comprueba que el esquema que producen y los modelos ORM
  coinciden: un cambio de esquema sin su modelo (o al revés) la rompe.

## Cómo agregar algo

**Un caso de uso nuevo en un contexto existente**

1. Si hay una regla, va en el agregado (`domain`), con su prueba pura.
2. Escribe el comando o la consulta y su manejador en `application`. Lo que necesite del
   exterior es un puerto de salida (un `Protocol`), no una clase concreta.
3. Implementa el puerto en `infrastructure` (persistencia, Keycloak, correo) y prueba el
   adaptador.
4. Expón el endpoint en `presentation/http`, con su esquema y la traducción de errores.
5. Cabléalo en `bootstrap/container.py` y en `app.py`.
6. Pruebas de cada capa y `make verify` en verde (100 % de cobertura).

**Un contexto nuevo:** crea `src/agilina_api/<contexto>/` con solo las capas que necesite,
agrégalo a los contratos de `import-linter` en el `pyproject.toml` y, si necesita algo de
otro contexto, declara el puerto y su adaptador en `bootstrap/`.

**Un texto para el usuario** (por ejemplo un correo) va en una plantilla en ES y en EN
(`shared/infrastructure/mail/`), nunca escrito en el caso de uso.

## Calidad (Definition of Done)

- `ruff`, `mypy --strict` y los contratos de arquitectura en verde.
- La lógica nueva lleva pruebas de cada capa que toca, y la cobertura de `api/src` y
  `shared/src` se mantiene en **100 %**.
- Todo texto dirigido al usuario existe en español y en inglés.
- Los errores se manejan y se registran; no se tragan en silencio.
- No se revisa formato ni estilo en el Code Review: de eso se encargan `ruff` y `mypy`.
