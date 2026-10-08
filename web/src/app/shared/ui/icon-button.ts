import { Directive } from '@angular/core';

/**
 * The look of a button that is only an icon (the eye that opens a detail, the bin that
 * removes): a square without border that lights up on hover. Put it on a native `<button>`
 * and name it with `aria-label`, since there is no text: `<button aglIconButton
 * aria-label="Remove Ana">…</button>`. Color of the icon is the current text color.
 */
@Directive({
  selector: 'button[aglIconButton]',
  host: {
    class:
      'inline-flex size-9 shrink-0 cursor-pointer items-center justify-center rounded-md ' +
      'text-foreground transition-colors hover:bg-accent/10 ' +
      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ' +
      'disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent',
  },
})
export class IconButton {}
