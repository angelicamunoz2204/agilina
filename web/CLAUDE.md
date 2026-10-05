@README.md

## Para agentes que trabajan en web/

- La guía de arriba manda. Si algo no está decidido ahí, en `docs/` ni en
  [AD-26](../docs/adr/0026-organizar-y-equipar-la-aplicacion-web.md), **pregunta
  antes de decidir**: no se inventan herramientas, librerías ni convenciones.
  La sección «Por decidir» lista lo que sigue abierto.
- Código, comentarios, nombres de archivo y claves de i18n en inglés. Commits,
  pull requests y documentación en español.
- Los estilos son **clases de Tailwind CSS** en la plantilla (sección «Estilos» de la
  guía y [AD-27](../docs/adr/0027-dar-estilo-a-la-web-con-tailwind-css.md)): colores
  solo de los tokens `--agl-*` (`bg-surface`, `text-muted`, `text-danger`…), nunca valores
  sueltos; un `.scss` de componente es la excepción; lo que se repite va a `shared/ui`
  (`aglButton`, `aglTextField`). El orden de las clases lo pone `make format`.
- Todo corre en contenedores: el Node de la máquina puede no servir para
  Angular 22. Usa `make lint`, `make test-web`, `make format` y `make verify`.
- Antes de dar algo por terminado: `make verify` en verde (formato, lint,
  compilación y pruebas).
- Commits: un solo autor, sin `Co-Authored-By` ni líneas de atribución.
