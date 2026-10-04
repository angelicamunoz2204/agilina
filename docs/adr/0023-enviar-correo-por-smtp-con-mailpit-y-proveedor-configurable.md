# AD-23: enviar correo por SMTP, con Mailpit en desarrollo y el proveedor por configuración

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-03
- **Deciden:** Diego, Angélica
- **Historia:** HU-02

## Contexto

HU-02 y HU-06 envían por correo el enlace de activación, y la arquitectura lista un
componente "Correo" sin nombrar proveedor. Los hechos que condicionan la decisión:

- **Aún no hay dominio propio.** La nube exige "dominio estable" (vista de despliegue)
  y todavía no está asignado. Sin dominio, ningún proveedor puede autenticar (SPF,
  DKIM, DMARC) a un remitente `@gmail.com` o `@universidad.edu`, de modo que los
  correos tienden a caer en spam o a rechazarse.
- **Sí hay cuenta de AWS** para el proyecto (AD-18).
- Las pruebas automáticas y la CI no pueden depender de un servicio externo: sería
  lento, inestable, con cuotas y con credenciales en la CI.
- El proyecto es educativo: el costo debe ser mínimo y no debe haber envíos reales por
  accidente durante el desarrollo.
- Los planes gratuitos cambian (SendGrid retiró el suyo en mayo de 2025). Los datos de
  proveedores de este ADR salen de comparativas de terceros consultadas el 2026-10-03
  y deben confirmarse en las páginas oficiales antes de contratar.

## Decisión

- El código envía correo a través de un **puerto `Mailer`** (`shared/application`), con
  un **adaptador SMTP estándar** (`SmtpMailer`) que admite conexión sin cifrar,
  STARTTLS (puerto 587) y TLS directo (puerto 465).
- **Los correos se arman con plantillas**, no con texto en el código: un puerto
  `EmailRenderer` y su implementación con Jinja2 (HTML con *autoescape*, más la versión
  de texto plano), con los textos en español y en inglés en un solo módulo. Los casos
  de uso piden "la invitación en español" y no conocen HTML ni el motor de plantillas.
- **Qué servidor entrega es solo configuración** (`AGILINA_SMTP_HOST`, `_PORT`, `_USER`,
  `_PASSWORD`, `_SECURITY` y `AGILINA_MAIL_FROM`), nunca código. Cambiar de proveedor,
  o pasar al dominio propio, es cambiar esas variables y los registros DNS.
- **Mailpit es el destino por defecto en local y en la CI.** Las pruebas automáticas
  leen el correo por su API. Nada sale de la máquina.
- **El proveedor real queda configurable desde ya**, con **Amazon SES en modo
  *sandbox*** como primer camino: se verifican direcciones individuales (la del
  remitente y las del equipo) y se prueba con `make mail-test`.
- **Quedan para HU-38:** el dominio y el proveedor de producción. Con dominio propio se
  verifica en el proveedor (SPF, DKIM, DMARC) y se pide salir del *sandbox*. Candidatos:
  SES (por AD-18) y Brevo.
- **No se usa el correo de la universidad** ni como cuenta SMTP ni como dominio de
  envío: depende de políticas ajenas, expone una identidad personal y caduca con la
  matrícula.

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| Proveedor real desde ya, sin Mailpit | La CI y las pruebas dependerían de internet, de cuotas y de secretos; cada prueba mandaría un correo real |
| Solo Mailpit hasta el despliegue | No ejercita las particularidades del proveedor (STARTTLS, autenticación, rechazo de destinatarios no verificados); se descubrirían tarde |
| Gmail SMTP como camino principal | 500 destinatarios por día, límites de comportamiento no publicados y un remitente atado a una cuenta personal. Queda como alternativa de emergencia con una cuenta dedicada al proyecto |
| Correo institucional como cuenta SMTP | Depende de la política del administrador (contraseñas de aplicación, y *Basic auth* de Microsoft 365 se desactiva por defecto desde diciembre de 2026), pone una identidad personal en la configuración y deja de existir al terminar el programa |
| SendGrid | Sin plan gratuito desde mayo de 2025 (prueba de 60 días y luego de pago) |
| Brevo desde ya | No autentica remitentes de dominios de correo gratuito; necesita dominio propio |

## Consecuencias

- **Fácil:** probar HU-02 de punta a punta sin internet; cambiar de proveedor o pasar al
  dominio propio sin tocar código; validar credenciales sin esperar una funcionalidad
  (`make mail-test`).
- **Difícil:** mantener dos caminos (Mailpit y el real) y recordar cuál está activo en
  cada entorno. En *sandbox* SES solo entrega a destinatarios verificados (alrededor de
  200 correos por día), y sin dominio propio los correos pueden llegar a spam.
- **Por verificar:** el *handshake* real con SES (STARTTLS y autenticación) no se ha
  probado; las pruebas del adaptador usan un `smtplib` simulado y la prueba real se hace
  con `make mail-test` al configurar SES. También los datos del proveedor, ver arriba.
- **Revertirla:** barata. Es una configuración y un adaptador pequeño detrás de un
  puerto.
