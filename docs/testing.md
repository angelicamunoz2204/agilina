# Cómo se prueba

Guía práctica de las pruebas de Python. La decisión y sus motivos están en
[AD-25](adr/0025-organizar-las-pruebas-con-arbol-espejo-builders-y-cobertura-total.md); las
reglas generales de código, en [code-conventions.md](code-conventions.md).

## Dónde van

```
tests/
├── api/
│   ├── builders/       Data Builders: cómo se arman los datos
│   ├── doubles/        Dobles en memoria de los puertos
│   ├── conftest.py     Reloj de identificadores, entorno y cliente HTTP
│   ├── unit/           Sin servidores: corre en segundos
│   │   ├── shared_kernel/  shared/{application,infrastructure,presentation}/
│   │   ├── identity/{domain,application,presentation,infrastructure}/
│   │   ├── teams/{domain,application}/   ceremonies/presentation/   bootstrap/
│   └── integration/    PostgreSQL y Keycloak reales, misma estructura que unit/
├── agent/unit/   stt/unit/   shared/unit/
```

**La ruta de una prueba es la de su módulo en `src/`.** Para saber dónde probar
`identity/application/commands/activate_account.py`, busca
`tests/api/unit/identity/application/commands/test_activate_account.py`. Los nombres de
archivo se repiten entre `unit/` e `integration/`; por eso pytest usa
`--import-mode=importlib`.

## Qué se prueba en cada capa

| Capa | Cómo | Árbol |
| --- | --- | --- |
| `domain` | Unitarias puras, con builders, sin dobles | `unit/` |
| `application` | Casos de uso con los dobles en memoria de `doubles/` | `unit/` |
| `presentation` | La aplicación real con un cliente HTTP y los casos de uso doblados | `unit/` |
| `infrastructure` | Repositorios y consultas contra PostgreSQL real; Keycloak con `httpx.MockTransport` y, además, contra el real; SMTP con un `smtplib` falso. Los errores que un servidor real casi no produce (una restricción desconocida, un fallo de red) se simulan con `doubles/database.py` | `integration/` y `unit/` |
| `bootstrap` | El grafo se construye sin conectarse, la aplicación registra sus rutas, el ciclo de vida arranca y para el planificador, y los comandos del operador (`make invite`, `make mail-test`) leen sus argumentos | `unit/`; los flujos con base de datos, en `integration/` |

## Los *Data Builders*

```python
from tests.api.builders import InvitationBuilder, TeamBuilder, next_id

invitation = InvitationBuilder().for_team(team_id).as_admin().build()
used       = InvitationBuilder().accepted_by(next_id()).build()
overdue    = InvitationBuilder().past_its_deadline().build()
replaced   = InvitationBuilder().revoked().build()
left       = TeamBuilder().with_admin(ana).with_removed_member(bruno).build()
await InvitationBuilder().for_team(team.id).saved_in(uow.invitations)
```

| Builder | Qué arma |
| --- | --- |
| `TeamBuilder` | Un equipo; `with_member`, `with_admin` y `with_removed_member` (entra y luego sale por `Team.remove_member`, así que el único admin no se puede remover tampoco aquí) |
| `InvitationBuilder` | Una invitación pendiente; `accepted_by`, `past_its_deadline`, `expired` y `revoked` (reemplazada por otra, con `Invitation.revoke`) |
| `AppUserBuilder` | Una cuenta de Agilina; `disabled` (una cuenta desactivada: ningún comportamiento la desactiva todavía, así que se restaura tal como se guarda) |
| `IssueInvitationBuilder`, `ActivateAccountBuilder`, `RequestNewInvitationBuilder` | Los comandos de invitación y activación (HU-02) |
| `InviteToTeamBuilder` | Un admin invita a alguien a su equipo (HU-06); `by_admin(user_id, membership_id)` fija quién invita y la membresía que queda como autora |
| `ChangeMemberRoleBuilder`, `RemoveMemberBuilder` | Un admin cambia el rol de un integrante o lo saca del equipo (HU-06) |
| `ContactBuilder`, `TeamContactsBuilder`, `EmailMessageBuilder` | Datos de lectura y mensajes de correo |

Reglas:

- Los valores por defecto son **válidos y fijos**; un fallo se reproduce igual cada vez.
- Cada `with_…`/`as_…` devuelve **un builder nuevo**: un builder compartido como punto de
  partida no se altera.
- `build()` usa las **reglas del dominio** (`Invitation.issue`, `Team.create`): si el
  dato es inválido, falla igual que en producción.
- Un estado se alcanza **por comportamiento** (`accepted_by` llama a `accept`, `revoked` a
  `revoke`, `with_removed_member` a `Team.remove_member`), nunca escribiendo atributos
  privados. Un estado guardado al que ningún comportamiento llega se restaura con
  `restored_as(...)`.
- `saved_in(repositorio)` sirve para el doble en memoria y para el repositorio SQL.
- En integración, `tests/api/integration/support.py` guarda con *commit* un equipo, un
  usuario o una invitación como datos de partida. La base impide dos invitaciones con el
  mismo token o dos usuarios con el mismo correo: `with_unique_token()` y
  `with_unique_email()` evitan el choque. Un integrante removido se guarda con
  `stored_team(session_factory, TeamBuilder()….with_removed_member(user_id))`, no con un
  `UPDATE` directo. `stored_sprint(session_factory, team_id, status)` es la excepción: el
  sprint todavía no tiene agregado (llega con HU-07), así que escribe la fila tal cual.
- Si te falta un builder, **agrégalo en `builders/`**, no en el archivo de la prueba.

## Los dobles

En `tests/api/doubles/`, uno por puerto, en memoria. Los que más se usan:

| Doble | Puerto | Qué permite |
| --- | --- | --- |
| `FakeClock` | `Clock` | Fija la hora y la avanza |
| `FakeMailer`, `FakeRenderer` | `Mailer`, `EmailRenderer` | Ver lo enviado (`sent`), hacer fallar el envío (`fail = True`) y leer la plantilla y sus parámetros en el cuerpo |
| `FakeTokenGenerator` | `ActivationTokenGenerator` | Entrega los tokens que le das, en orden |
| `FakeIdentityProvider` | `IdentityProvider` (Keycloak) | Crea o borra cuentas, rechaza una contraseña o se cae |
| `FakeAuthenticatedUsers` | `AuthenticatedUsers` | Hace de inicio de sesión mientras no exista HU-03: cada token es un usuario |
| `FakeTeamAccess`, `FakeTeamQueries` | `TeamAccess`, `TeamQueries` | La membresía y el rol de cada usuario, y lo que leen las consultas |
| `FakeActiveSprints` | `ActiveSprints` | Los equipos que tienen un sprint en curso |
| `FakeMemberContacts` | `MemberContactsDirectory` | El nombre y el correo de cada integrante; los demás no tienen cuenta |

### Flujos de punta a punta

Una historia se prueba completa por HTTP contra PostgreSQL real, sin inicio de sesión, con
el patrón de `tests/api/integration/teams/presentation/http/test_teams_flow.py`:
`create_app()` con `dependency_overrides` hacia los *handlers* reales, `FakeAuthenticatedUsers`
en lugar del login, `SqlTeamQueries` como `TeamAccess` (la membresía se comprueba contra la
tabla) y solo el correo, los tokens y el reloj doblados.

Para los casos de uso que cruzan identity y teams sin pasar por HTTP,
`tests/api/integration/world.py` arma `World`: base real, repositorios reales y los mismos
dobles. Tiene la invitación y la activación de HU-02 y, de HU-06, `invite_to_team`,
`list_members`, `change_role` y `remove`; `admin_invites(team_id, admin_id, …)` invita
como lo hace la ruta, con la membresía del admin como autora. Escribe los correos con
`FakeRenderer` (plantilla y parámetros); `World(session_factory, JinjaEmailRenderer())` usa
las plantillas reales cuando la prueba necesita leer lo que recibe la persona.

## Reglas de cada prueba

- Describe un comportamiento, no un método: `test_an_expired_link_cannot_be_used`.
- No depende de otra ni del orden; el reloj es `FakeClock` y los identificadores salen de
  `next_id()` (un contador que se reinicia en cada prueba).
- Una prueba no tiene condicionales sobre el entorno (`if status == 503`): si depende de
  un servidor, se simula o va a `integration/`.
- Todo error corregido deja una prueba que lo habría detectado.

## Comandos

| Quiero… | Comando |
| --- | --- |
| Las pruebas unitarias | `make test-python` |
| Las de integración (levanta PostgreSQL) | `make test-integration` |
| Las del adaptador de Keycloak real | `make test-keycloak` |
| La cobertura, con el umbral del 100 % | `make coverage` |
| Todo lo que corre la CI | `make verify` |

## Cobertura

La API (`api/src`) y el contrato (`shared/src`) están en **100 % de líneas y ramas**,
sumando unitarias e integración, y la CI falla por debajo. Las pruebas de Keycloak real
(`make test-keycloak`) no cuentan para el umbral: el adaptador ya se cubre con el servidor
simulado, y la CI no levanta Keycloak. `agent/` y `stt/` no están en el umbral todavía.

Una línea que no se pueda probar se excluye con `# pragma: no cover` y una razón al lado,
o por las reglas de `pyproject.toml` (cuerpos de un `Protocol`, `if __name__ == "__main__"`).
Agregar una exclusión es una decisión que se revisa en el pull request.
