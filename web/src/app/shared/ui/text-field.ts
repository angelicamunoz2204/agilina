import { Directive } from '@angular/core';

/**
 * The look of a text box. Put it on a native `<input>`; its label is a `<label for>` next
 * to it, which this directive does not replace: `<input aglTextField id="password" />`.
 */
@Directive({
  selector: 'input[aglTextField]',
  host: {
    class:
      'block min-h-11 w-full rounded-md border border-border bg-transparent px-3 py-2 ' +
      'text-foreground shadow-sm focus-visible:outline-2 focus-visible:outline-offset-1 ' +
      'focus-visible:outline-accent aria-invalid:border-danger',
  },
})
export class TextField {}
