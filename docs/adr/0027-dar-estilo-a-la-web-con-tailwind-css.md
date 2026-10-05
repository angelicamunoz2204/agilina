# AD-27: dar estilo a la web con Tailwind CSS

- **Estado:** propuesta (pasa a aceptada al integrarse este PR)
- **Fecha:** 2026-10-04
- **Deciden:** Diego, Angélica
- **Historia:** HU-02 (la pantalla `/activar` es la primera que lo usa)

## Contexto

La web tenía dos pantallas, estilos en un `.scss` por componente y unos tokens `--agl-*`
provisionales. Las guías dejaban abierto el «sistema de diseño para `shared/ui`». Con las
historias de identidad, equipos y la sala por empezar, cada pantalla habría decidido su propio
estilo. Los hechos que pesaron:

- **Los mockups** (prototipo de Lovable, `context/mockups.md`) son una referencia visual de
  muchas pantallas: dashboard, tablas, diálogos, modo claro y oscuro, diseño adaptable.
- **Angular 22 lo soporta de fábrica** ([guía](https://angular.dev/guide/tailwind)): se instala
  `tailwindcss`, `@tailwindcss/postcss` y `postcss`, y `@angular/build` ya lo declara como
  dependencia opcional.
- **Hoy hay solo dos pantallas**, así que migrar cuesta poco; más adelante costaría más.

## Decisión

- **Tailwind CSS 4**, por PostCSS (`.postcssrc.json`), con el CSS de entrada en
  `src/styles.css` (antes `styles.scss`). Los estilos de una pantalla son **clases de utilidad
  en su plantilla**, no una hoja por componente.
- **Los tokens siguen siendo `--agl-*`** y son la fuente de verdad: Tailwind los lee como tema
  (`@theme inline`) y por eso hay `bg-surface`, `text-muted`, `border-border`, `text-danger`…
  Un tema (claro u oscuro) es otro juego de valores de esas variables, sin tocar plantillas.
- **Lo que se repite se vuelve una pieza de `shared/ui`**, no un grupo de clases copiado:
  directivas sobre elementos nativos (`button[aglButton]`, `input[aglTextField]`), para que el
  teclado y los lectores de pantalla sigan funcionando. No se usa `@apply` para esto.
- **El orden de las clases lo pone Prettier** con `prettier-plugin-tailwindcss`.
- **Un `.scss` de componente solo para lo que las utilidades no expresan** (por ejemplo una
  animación); es la excepción y se justifica en la revisión.

## Alternativas descartadas

- **Seguir con SCSS por componente:** funciona, pero cada pantalla nueva repite resets,
  espacios y estados, y el mockup no se traduce directamente.
- **Una librería de componentes ya hecha como base de estilo:** es una decisión aparte y mayor
  (control del diseño, peso, accesibilidad). Se deja abierta.
- **Tailwind con `@apply` en hojas por componente:** vuelve a una hoja por componente y
  esconde las clases; se usa solo si algún día hace falta.

## Consecuencias

- Las plantillas quedan más largas. Lo compensan las piezas de `shared/ui` y el ordenado
  automático de clases.
- El presupuesto de 4 kB por hoja de estilos de componente deja de ser la medida principal; el
  que importa es el del CSS global, que Tailwind genera solo con las clases que se usan.
- Una prueba no debe buscar un elemento por su clase de estilo (`.brand`): usa el texto, el rol
  o la etiqueta.
- **Sigue abierta** la «librería de componentes» para `shared/ui` (diálogos, tablas, menús):
  si se adopta una, que se apoye en Tailwind.
- Tailwind 4 pide navegadores modernos (Chrome 111, Safari 16.4 y Firefox 128 o posteriores).
  Es una restricción aceptable para una aplicación de uso interno de equipos.

## Cómo se verifica

`make lint`, `make test-web` y `make verify` en verde, y las pantallas existentes se ven igual
que antes (revisadas en escritorio y móvil).
