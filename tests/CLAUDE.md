## Para agentes que escriben pruebas de Python

Estas son las pruebas de `api/`, `agent/`, `stt/` y `shared/`, y las de punta a punta (`tests/e2e`, Playwright, `make test-e2e`). La guía práctica es
[docs/testing.md](../docs/testing.md) y la decisión, [AD-25](../docs/adr/0025-organizar-las-pruebas-con-arbol-espejo-builders-y-cobertura-total.md).
Si algo no está decidido ahí, **pregunta antes de decidir**. Las pruebas de la web no están
aquí: viven junto a su código, en `web/src`, y se rigen por [web/CLAUDE.md](../web/CLAUDE.md).

- Código, nombres y descripciones de las pruebas en inglés. Commits y documentación en
  español.
- Todo corre en contenedores: `make test-python` (unitarias), `make test-integration`
  (PostgreSQL real), `make test-keycloak` (Keycloak real), `make coverage` (umbral del
  100 %) y `make verify` (lo que corre la CI). Antes de dar algo por terminado,
  `make verify` en verde.
- Commits: un solo autor, sin `Co-Authored-By` ni líneas de atribución. Nada de commits ni
  push sin autorización explícita.

## Dónde va una prueba

```
tests/<pieza>/{unit,integration}/<ruta del módulo en src/>/test_<módulo>.py
tests/api/builders/   Data Builders          tests/api/doubles/   dobles de los puertos
```

**La ruta de la prueba es la del módulo que prueba.** `identity/application/commands/activate_account.py`
se prueba en `tests/api/unit/identity/application/commands/test_activate_account.py`. Lo que
necesita PostgreSQL o Keycloak reales va en `integration/`, en la misma ruta, con
`pytestmark = pytest.mark.integration` (o `keycloak`). Una prueba nueva se mueve con su
módulo cuando este se mueve.

## Qué se prueba en cada capa

| Capa | Cómo |
| --- | --- |
| `domain` | Unitarias puras, con builders, sin dobles ni servidores |
| `application` | Casos de uso con los dobles en memoria de `doubles/`, que cumplen el mismo `Protocol` que los adaptadores |
| `presentation` | La aplicación real con un cliente HTTP y los casos de uso doblados; verifican el contrato (estado, código de error, cabeceras), no la lógica |
| `infrastructure` | Repositorios y consultas contra PostgreSQL real; Keycloak con `httpx.MockTransport` y además contra el real; SMTP con un `smtplib` falso. Un error que un servidor real casi no produce se simula con `doubles/database.py` |
| `bootstrap` | El grafo se construye sin conectarse, la aplicación registra sus rutas, el ciclo de vida arranca y para el planificador, y los comandos del operador leen sus argumentos |

## Cómo se escribe

- **Los datos se arman con Data Builders, nunca con funciones sueltas ni a mano.**
  `InvitationBuilder().for_team(team_id).as_admin().build()`. Los valores por defecto son
  válidos y fijos; cada `with_…`/`as_…` devuelve un builder nuevo; `build()` pasa por las
  reglas del dominio; un estado se alcanza por comportamiento (`accepted_by` llama a
  `accept`), no escribiendo atributos privados. Si falta uno, **se agrega en `builders/`**,
  no dentro del archivo de la prueba.
- **El tenant también es un dato de prueba:** `TenantBuilder` (acme, en inglés; `.ecomoda()` el
  otro) y `FakeTenantDirectory` en las unitarias; en integración, `platform_databases` crea un
  catálogo y las bases de `acme` y `ecomoda`, y `session_factory` / `ecomoda_session_factory` son
  las de cada uno. Una prueba que muestra aislamiento usa los dos y comprueba que no se mezclan.
- **Los identificadores salen de `next_id()`**, un contador que se reinicia en cada prueba;
  no uses `uuid4()` ni `datetime.now()`. El reloj es `FakeClock`.
- Una prueba describe un comportamiento, no un método: `test_an_expired_link_cannot_be_used`.
- Una prueba no depende de otra ni del orden, y no tiene condicionales sobre el entorno
  (`if status == 503`): si depende de un servidor, se simula o va a `integration/`.
- En integración, los datos de partida se guardan con `tests/api/integration/support.py`;
  la base impide dos invitaciones con el mismo token o dos usuarios con el mismo correo, así
  que usa `with_unique_token()` y `with_unique_email()`.
- Un doble en memoria guarda y devuelve **copias**, como la base: un cambio que no se guarda
  se pierde con la transacción.
- Todo error corregido deja una prueba que lo habría detectado.

## Cobertura

`api/src` y `shared/src` están al **100 % de líneas y ramas**, sumando unitarias e
integración, y la CI falla por debajo. Una prueba nueva no puede bajarla: si una línea no se
puede probar, se excluye con `# pragma: no cover` y la razón al lado, o por las reglas de
`pyproject.toml`; esa exclusión se justifica en el pull request. `agent/` y `stt/` entran al
umbral cuando sus historias escriban sus pruebas con este mismo esquema.
