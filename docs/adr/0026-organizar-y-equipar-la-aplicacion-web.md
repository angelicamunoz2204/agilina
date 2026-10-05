# AD-26: organizar y equipar la aplicación web

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-04
- **Deciden:** Diego, Angélica
- **Historia:** ninguna; gestión de configuración (Sprint-0)

## Contexto

La web llegó del Sprint 0 con Angular 20 sobre zone.js, un servicio de textos
propio, ESLint sin formateador, URLs escritas en `environment.ts` y una sola
funcionalidad (`status`) organizada en las cuatro capas de AD-21. Las reglas de
la web ya fijaban Angular 22 zoneless con signals, configuración por variables
de entorno y textos en dos idiomas, pero dejaban abiertas cuatro decisiones: la
herramienta de lint y formato, la librería de i18n, la estructura de carpetas y
el estándar de registro de errores. Con las historias de identidad, equipos y la
sala a punto de empezar, dejarlas abiertas significa que cada historia las
decida a su manera.

## Decisión

- **Angular 22, zoneless y `OnPush` por defecto,** con TypeScript 6 estricto
  (más `noUncheckedIndexedAccess` y `exactOptionalPropertyTypes`). Las lecturas
  de datos usan `rxResource`; rxjs queda en los bordes.
- **ESLint + Prettier.** Prettier decide el formato (TS, HTML, SCSS, JSON);
  ESLint, con reglas *type-checked*, `angular-eslint` (incluidas las de
  accesibilidad) e `import-x`, hace cumplir el resto. `eslint-config-prettier`
  evita que choquen. La CI y `make verify` corren `format:check` y
  `lint --max-warnings=0`.
- **Transloco** para los textos, con los catálogos en `public/i18n`, cambio de
  idioma en caliente (el idioma es del equipo y llega de la API) y un manejador
  que registra las claves faltantes.
- **Estructura `core/`, `layout/`, `shared/` y `features/<contexto>/` con las
  cuatro capas de AD-21,** alias de ruta (`@core/*`, `@shared/*`, `@layout/*`,
  `@features/*`, `@testing/*`) y fronteras verificadas sobre el archivo
  resuelto con `import-x/no-restricted-paths`: capas hacia adentro, ninguna
  funcionalidad importa a otra y `core`/`shared` no conocen las funcionalidades.
- **Registro de errores con un puerto `Logger`** de entradas estructuradas
  (nivel, mensaje, *timestamp* UTC, contexto, error), un adaptador de consola,
  un `ErrorHandler` global y un interceptor HTTP. Cada error se registra una
  vez, donde se maneja; `console.*` está prohibido fuera del adaptador.
- **Configuración en tiempo de ejecución:** `config.json` se genera desde
  variables de entorno al arrancar el contenedor (nginx con `envsubst` en
  producción, un script en desarrollo) y se valida antes de arrancar Angular.

El detalle está en [web/README.md](../../web/README.md).

## Alternativas descartadas

| Alternativa | Por qué no |
| --- | --- |
| ESLint + Prettier + Stylelint | Una herramienta más para pocas hojas de estilo; se reconsidera si el SCSS crece |
| Biome para el formato | Todavía formatea mal las plantillas de Angular |
| Solo ESLint con `@stylistic` | No formatea HTML ni SCSS |
| `@angular/localize` | Compila un bundle por idioma: cambiar de idioma exige recargar otra compilación, y el idioma llega del equipo en tiempo de ejecución |
| ngx-translate | Funciona, pero sin carga por funcionalidad ni herramientas para claves |
| Mantener el servicio de textos propio | Sin interpolación, plurales ni carga diferida: habría que construirlos |
| Funcionalidades sin capas (guía de estilo de Angular) | Pierde la simetría con la API y las reglas de capas que ya verifica la CI |
| Tipos de librería al estilo Nx (`feature`, `ui`, `data-access`, `util`) | Otro vocabulario distinto al de la API para la misma idea |
| Fronteras con `no-restricted-imports` por patrones | Mira el texto del `import`, no el archivo: un `../../` cruzaba de funcionalidad sin que se notara |
| Enviar los registros a la API, Sentry u OpenTelemetry desde ya | Requiere trabajo o servicios fuera de la web; el puerto deja la puerta abierta sin cambiar a quien registra |
| `environment.ts` por entorno | Obliga a compilar una imagen por entorno y deja URLs en el código |

## Consecuencias

- **Fácil:** que una historia nueva caiga en el lugar correcto; detectar en la
  CI una violación de capas o un `console.log`; cambiar el destino de los
  registros o el proveedor de identidad escribiendo un adaptador; desplegar la
  misma imagen en local y en la nube.
- **Difícil:** más archivos por funcionalidad (puerto, adaptador, *facade*);
  ESLint *type-checked* es más lento; la web no arranca si falta una variable
  de entorno (a propósito).
- **Por verificar:** que Karma siga siendo viable; Angular usa Vitest por
  defecto desde la versión 21 y Karma está archivado. Migrar es cambiar el
  *builder* y las aserciones de Jasmine.
- **Revertirla:** barata mientras haya una sola funcionalidad; cada
  funcionalidad nueva la encarece.
