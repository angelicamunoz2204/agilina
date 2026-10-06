# Glosario del dominio (lenguaje ubicuo)

Un concepto tiene **un solo nombre** en el código, en la base de datos, en la
API y en la conversación del equipo. Esta tabla fija ese nombre en inglés (el
del código) y su equivalente en español (el de la documentación y el producto).
Si aparece un concepto nuevo, se agrega aquí antes de usarlo.

## Equipos y personas

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| `Team` | Equipo | Conjunto de personas que hace la daily. Es el **tenant**: todo dato de negocio pertenece a un equipo |
| `TeamMember` (membresía) | Integrante | La pertenencia de una persona a un equipo, con su rol. Una persona puede tener roles distintos en equipos distintos |
| `AppUser` | Usuario | La identidad de una persona en Agilina; su contraseña y sus sesiones viven en Keycloak |
| `TeamRole` | Rol | El rol **interno** por equipo: `admin` o `member`. Es lo único contra lo que se autoriza |
| `admin` | Administrador | Rol que gestiona el equipo. En modo soporte se muestra como **Scrum Master** |
| `member` | Miembro | Rol de quien participa en la daily |
| Visible label | Etiqueta visible | Cómo se rotula un rol en pantalla (Administrador, Scrum Master o Miembro). Se **deriva** de rol + modo; no se guarda |
| Platform operator | Operador de la plataforma | Quien administra la instalación (no es un integrante); emite la invitación del primer Administrador |
| `TeamSelector` | Selector de equipo | Pantalla con los equipos a los que pertenece el usuario, para entrar a uno o crear uno nuevo |
| `TeamDashboard` | Dashboard del equipo | Pantalla de entrada a un equipo, a la que se llega desde el selector o al crearlo |

## Acceso

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| `Invitation` | Invitación | Permiso de un solo uso para entrar a un equipo con un rol. No hay registro público |
| `ActivationToken` | Token de activación | Secreto de un solo uso que viaja en el enlace de la invitación. Solo se guarda su hash |
| Activation | Activación | Aceptar una invitación: definir la contraseña y quedar como integrante del equipo con el rol asignado |
| `InvitationStatus` | Estado de la invitación | `pending`, `accepted`, `expired` o `revoked`. Caduca a los 7 días |
| Keycloak subject | Sujeto de Keycloak | El `sub` del token; la única unión entre `AppUser` y el proveedor de identidad |

## Modo y configuración

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| `OperationMode` | Modo de operación | `support` (soporte) o `autonomous` (autónomo). Su único efecto: si Agilina pide aprobación antes de ejecutar una acción |
| `support` | Modo soporte | Un Scrum Master humano aprueba las acciones |
| `autonomous` | Modo autónomo | Agilina ejecuta y luego informa |
| `Language` | Idioma | `es` o `en`. Atributo del equipo; parametriza transcripción, plantillas, voz y resumen |
| `Sprint` | Sprint | Periodo de trabajo del equipo. Puede estar `planned`, `active` o `closed` |
| `SprintStatus` | Estado del sprint | `planned`, `active` o `closed`. Un equipo tiene a lo sumo un sprint `active`; mientras dura no se cambian roles (HU-06) |
| `MemberPreference` | Preferencia del integrante | Hora y zona del recordatorio matutino; lo único que el rol Miembro configura |

## La ceremonia

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| `Ceremony` | Ceremonia | Una ocurrencia de la reunión. Hoy solo existe el tipo `daily` |
| Daily | Daily | La reunión diaria de pie (*stand-up*) |
| `CeremonyStatus` | Estado de la ceremonia | `scheduled`, `in_progress`, `completed`, `cancelled`. El contrato del worker agrega `degraded`, que el esquema aún modela como bandera `degraded` de la ceremonia (a resolver en HU-56) |
| `CeremonyContext` | Contexto de la ceremonia | Lo que el worker necesita saber antes de entrar a la sala |
| `CeremonyResult` | Resultado de la ceremonia | Lo que el worker entrega a la API al cerrar |
| `Roster` | Roster | Lista ordenada de los participantes convocados y su rol |
| Turn | Turno | El momento en que un participante habla; los turnos siguen un orden fijo |
| `turn_order` | Orden de turno | Posición del participante en la ronda |
| Silence threshold | Umbral de silencio (X) | Segundos de silencio tras los que Agilina pregunta |
| Stuck-turn threshold | Umbral de turno trabado (Y) | Segundos sin avance tras los que Agilina interviene |
| Wake word | Palabra de activación | Palabra con la que se le habla a Agilina durante la ceremonia |
| Degraded mode | Modo degradado | La transcripción no responde: Agilina lo anuncia y la ceremonia sigue sin facilitación automática |
| Room | Sala | La sala de audio de LiveKit de una ceremonia |
| `room_identity` | Identidad de sala | Identidad con la que alguien entra a LiveKit; con ella se atribuye lo que dice, sin diarización |
| `TranscriptSegment` | Segmento de transcripción | Fragmento final de texto atribuido a quien lo dijo, con marcas de tiempo |

## Lo que sale de la ceremonia

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| Blocker | Bloqueo | Impedimento detectado en la ceremonia |
| Issue mention | Mención de issue | Referencia a un ticket del tablero (Jira) |
| `ActionItem` | Action item | Acción derivada de la ceremonia, con su estado: propuesto, aprobado, rechazado, ejecutado o fallido. Rechazar no borra |
| `ApprovalRequest` | Solicitud de aprobación | En modo soporte, el mensaje de Slack con una casilla por action item |
| Post-processing | Post-procesamiento | El razonamiento con el LLM, una sola vez al cerrar la ceremonia (AD-19) |

## Arquitectura

| Código (EN) | Español | Qué es |
| --- | --- | --- |
| Bounded context | Contexto delimitado | Frontera dentro de la cual un término tiene un solo significado (`identity`, `teams`, `ceremonies`…) |
| Aggregate / aggregate root | Agregado / raíz | Grupo de objetos que se modifica como una unidad a través de su raíz |
| Value object | Objeto de valor | Valor inmutable definido por sus atributos y validado al crearse |
| Port | Puerto | Interfaz que el núcleo declara para hablar con el mundo exterior |
| Adapter | Adaptador | Implementación concreta de un puerto para un proveedor |
| Command / query | Comando / consulta | Operación que cambia estado / operación que solo lee |
| Composition root | Raíz de composición | El único lugar que enlaza puertos con adaptadores |
