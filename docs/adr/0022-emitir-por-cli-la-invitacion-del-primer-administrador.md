# AD-22: emitir por línea de comandos la invitación del primer administrador

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-03
- **Deciden:** Diego, Angélica
- **Historia:** HU-02

## Contexto

Agilina no tiene registro público: la única forma de entrar es una invitación
que genera un Administrador (HU-02, HU-06). Eso deja sin resolver cómo nace el
primer Administrador de la primera instalación. En el esquema, `invitation.created_by`
referencia a un `team_member` y `team.created_by` a un `app_user`, ambos
`NOT NULL`: para emitir la primera invitación ya haría falta un integrante, y
para que exista un integrante hace falta haber activado una invitación.

## Decisión

El **operador de la plataforma** crea el equipo y emite la invitación de su primer
Administrador con un comando de línea de comandos (`make invite`), que usa el
mismo caso de uso `IssueInvitation` que usará HU-06. Para que eso sea posible:

- `invitation.created_by` y `team.created_by` pasan a aceptar `NULL`. `NULL`
  significa "creado por el operador de la plataforma, no por un integrante". Los
  equipos que crea una persona ya autenticada (HU-05) siguen guardando su autor.
- El comando no se expone por HTTP: requiere acceso al entorno donde corre la
  API (y a su base de datos y a Keycloak), que es la frontera de confianza del
  operador. El flujo posterior (enlace de un solo uso, activación, rol y equipo)
  es exactamente el de cualquier otra invitación.
- El token se genera y se entrega como en cualquier invitación: solo se guarda
  su hash y el enlace se envía por correo.
- El DDL de referencia (`agilina_schema.sql`) y el resumen del modelo de datos
  se actualizan con este cambio, y la migración de HU-02 lo aplica.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Crear el primer usuario a mano en Keycloak y en la base de datos | Se salta el flujo de activación, no ejercita la HU-02 y obliga a mantener un procedimiento manual distinto por entorno |
| Registro público solo para el primer equipo | Contradice el criterio "no existe registro abierto" y deja una puerta abierta en producción |
| Un usuario o rol "administrador de plataforma" con endpoints propios | Agrega un tercer rol y una superficie de ataque que ningún requisito pide |
| Sembrar un usuario administrador con credenciales en el repositorio o en un *seed* | Una credencial por defecto es justamente lo que el Definition of Done prohíbe |

## Consecuencias

- **Fácil:** montar un entorno nuevo (local o nube) con un solo comando y probar
  la HU-02 de punta a punta desde la primera instalación.
- **Difícil:** `created_by` ya no garantiza por sí solo quién emitió una
  invitación; la trazabilidad de las que emite el operador queda en el registro
  de la aplicación y, cuando exista, en `audit_log`.
- **Por verificar:** que ninguna historia posterior (por ejemplo auditoría o
  reportes) asuma `created_by` no nulo.
- **Revertirla:** barata antes de que haya datos; después exigiría rellenar los
  `NULL` con un integrante o con una convención explícita.
