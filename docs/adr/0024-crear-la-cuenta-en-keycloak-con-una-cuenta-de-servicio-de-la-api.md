# AD-24: crear la cuenta en Keycloak con una cuenta de servicio de la API

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-04
- **Deciden:** Diego, Angélica
- **Historia:** HU-02

## Contexto

En HU-02 la persona define su contraseña al abrir el enlace de la invitación y su cuenta
queda creada en Keycloak con el rol y el equipo que fijó quien la invitó (criterios 2, 3
y 6). Keycloak es el dueño de las credenciales y las sesiones (AD-12) y la política
mínima de contraseñas "está configurada en Keycloak". La API necesita, entonces, una
forma de crear usuarios allí sin que el navegador hable con la Admin API.

Hay un fallo posible en medio: la cuenta se crea en Keycloak (un sistema externo) y la
base de datos de Agilina puede rechazar el resto de la activación. Las dos cosas no
pueden compartir una transacción.

## Decisión

- La API usa su **propio cliente confidencial `agilina-api`** (cuenta de servicio, flujo
  de credenciales de cliente). Solo tiene los roles `manage-users` y `view-users`: no
  puede administrar el realm ni leer otros datos. Su secreto es
  `AGILINA_KEYCLOAK_API_SECRET`, que `make env` genera y que Keycloak toma del entorno al
  importar el realm (`${AGILINA_KEYCLOAK_API_SECRET}`): no vive en el repositorio.
- **La política de contraseñas es la del realm**, versionada en `realm-agilina.json`:
  `length(12) and notUsername and notEmail`. La política concreta es una propuesta de
  producto (la historia solo pide "la política mínima configurada en Keycloak"). Keycloak
  la valida; la API traduce su respuesta a motivos estables (`min_length`, `not_username`,
  `not_email`, `other`) y la web los muestra en el idioma de la persona.
- **Orden de la activación:** primero se valida el estado del enlace en memoria (no se toca
  nada externo si ya fue usado, venció o fue revocado); luego se crea la cuenta en
  Keycloak; luego, en **una sola transacción**, se crean el usuario y la membresía y se
  marca la invitación como usada. Si algo de eso falla, se **borra la cuenta recién creada
  en Keycloak** (compensación) y se propaga el error original.
- La cuenta se crea **habilitada, con el correo verificado** (el enlace ya lo demostró) y
  **con la contraseña definitiva**, no temporal.
- Un correo que ya tiene cuenta se informa con un mensaje claro (`409`); vincular esa
  cuenta a otro equipo es HU-06.
- El nombre completo se guarda en Keycloak como nombre (la primera palabra) y apellido (el
  resto).
- Un cambio en `realm-agilina.json` solo se aplica con un Keycloak de volumen vacío:
  `make keycloak-reset` lo reimporta (borra los datos de Keycloak, no los de Postgres).

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Registro propio de Keycloak (`registrationAllowed`) con la invitación como filtro | Contradice "no existe registro público": cualquiera podría registrarse sin invitación |
| Que Keycloak envíe el correo (acción `UPDATE_PASSWORD`) | El estado del enlace (un solo uso, 7 días, equipo y rol) vive en Agilina; habría que duplicarlo en Keycloak y perder el control de la plantilla y del idioma |
| Usar las credenciales del administrador de Keycloak | Daría a la API poder sobre todo el realm: el cliente de servicio limita el daño de una filtración al manejo de usuarios |
| Crear el usuario sin contraseña y fijarla después | Deja una cuenta sin credencial si falla el segundo paso; crear con la credencial incluida es atómico en Keycloak |
| No compensar y reconciliar a mano | Un usuario huérfano bloquearía el correo (`409` en cada reintento) |

## Consecuencias

- **Fácil:** la API no guarda ninguna contraseña; el cambio de la política es editar un
  archivo versionado; una contraseña rechazada no deja nada atrás (comprobado contra el
  Keycloak real).
- **Difícil:** la compensación es de mejor esfuerzo. Si borrar la cuenta también falla
  (Keycloak caído justo entonces), queda un usuario huérfano que bloquea ese correo hasta
  borrarlo a mano; el fallo queda en el registro.
- **Por verificar:** que el inicio de sesión (HU-03) funcione con las cuentas creadas así;
  y la política de 12 caracteres, que es una propuesta.
- **Revertirla:** barata. El puerto `IdentityProvider` aísla a Keycloak; cambiar la
  política es una línea del realm.
