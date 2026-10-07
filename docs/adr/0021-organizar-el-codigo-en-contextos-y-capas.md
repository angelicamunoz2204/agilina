# AD-21: organizar el código en contextos y capas con arquitectura limpia

- **Estado:** propuesta (pasa a aceptada al integrarse este PR); en lo de «el equipo es el tenant», supersedida en parte por [AD-29](0029-un-tenant-es-una-organizacion-con-su-base-y-su-realm.md)
- **Fecha:** 2026-10-03
- **Deciden:** Diego, Angélica
- **Historia:** HU-02

## Contexto

El Sprint 0 dejó un esqueleto plano: la API tenía `rutas/` y `db/`, sin lugar
para reglas de negocio, y todo el código estaba en español. La HU-02 es la
primera historia con dominio real (invitaciones, usuarios, equipos) y a partir
de ella el código crece historia tras historia, escrito por dos personas fuera
de su horario laboral. AD-16 ya exige puertos y adaptadores para integraciones
y modelos, pero no dice cómo se organiza el resto. El producto es multi-tenant
(el equipo es el tenant) y debe poder desplegarse en la nube sin reescribirse.

## Decisión

El código se organiza **primero por contexto delimitado y después por capa**,
con arquitectura limpia y puertos y adaptadores:

- Cada contexto (`identity`, `teams`, `ceremonies`…) es un paquete directo bajo
  `agilina_api/`, con las capas que necesite: `domain`, `application`,
  `presentation` e `infrastructure`. Hay además `bootstrap/` (raíz de
  composición), `shared_kernel/` (bloques base del dominio) y `shared/`
  (transversal).
- La dependencia apunta hacia adentro: `presentation` e `infrastructure` →
  `application` → `domain`. `presentation` nunca importa `infrastructure`; solo
  se encuentran en la raíz de composición. Los contextos no se importan entre sí.
- **DDD táctico:** agregados con una raíz que protege sus invariantes, un
  repositorio por agregado (su interfaz vive en `domain`), objetos de valor
  inmutables y eventos de dominio. Los demás puertos de salida viven en
  `application`. Los modelos ORM no son las entidades del dominio: se convierten
  con mapeadores.
- **CQRS pragmático:** los comandos pasan por el agregado y una unidad de
  trabajo; las consultas leen directo con SQL y devuelven DTO. Una sola base de
  datos, sin *event sourcing* y sin bus genérico.
- **Multi-tenant por firma:** todo repositorio y consulta con datos de equipo
  exige el `team_id` como parámetro.
- **El código va en inglés** (identificadores, comentarios, rutas, campos JSON,
  variables de entorno, objetivos de `make`); commits, PR y documentación, en
  español. Los valores de los enums coinciden con los tipos de PostgreSQL.
- El worker, la transcripción y la web siguen las mismas cuatro capas, en la
  medida en que tienen dominio.
- Las reglas se hacen cumplir con herramientas: `import-linter`, `mypy
  --strict`, reglas de ESLint y `ruff`, en `make verify`, la CI y pre-push.

El detalle de carpetas está en [estructura-del-proyecto.md](../estructura-del-proyecto.md)
y las reglas de escritura en [code-conventions.md](../code-conventions.md).

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Primero la capa, después el contexto (`domain/identity`, `application/identity`…) | Una historia toca cuatro carpetas lejanas, el límite entre contextos no lo protege nada estructural y la raíz habla de técnica en vez de negocio |
| Capas planas sin contextos (el esqueleto del Sprint 0) | Mezcla reglas de negocio con FastAPI y SQLAlchemy: no se prueban sin base de datos y cambiar un proveedor toca todo |
| CQRS completo con almacén de lectura aparte, *event sourcing* o bus | Con dos personas y este volumen el costo de operar dos modelos no se recupera; queda como opción si algún día hace falta |
| Un mediador o bus genérico de comandos | Oculta el flujo; cada endpoint recibe su manejador por inyección, que es explícito y fácil de seguir |
| Separar `infrastructure` en adaptadores de interfaz y *frameworks* | En Python dejaría archivos casi vacíos: SQLAlchemy y `httpx` ya cumplen el papel de driver |
| Código en español | Decisión del equipo: el código en inglés evita mezclar idiomas con los nombres de bibliotecas y protocolos |

## Consecuencias

- **Fácil:** probar el dominio y los casos de uso sin base de datos ni red;
  cambiar de proveedor escribiendo un adaptador; repartir historias entre dos
  personas con pocos conflictos; detectar una violación de capas en la CI.
- **Difícil:** más archivos y más código por funcionalidad (mapeadores, DTO,
  puertos); el nombre de los contextos hay que acordarlo con cuidado porque
  mover uno después es un cambio grande.
- **Por verificar:** que el costo de los mapeadores ORM ↔ dominio sea razonable
  con las primeras tres entidades de HU-02; si no, se revisa esa parte antes de
  extender el patrón.
- **Revertirla:** barata mientras haya pocos contextos (mover carpetas y
  ajustar el contrato de `import-linter`); cada contexto nuevo la encarece.
