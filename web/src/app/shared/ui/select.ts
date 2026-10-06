import { Directive } from '@angular/core';

/**
 * The look of a drop-down list. Put it on a native `<select>`, so that keyboard and screen
 * readers keep working; its label is a `<label for>` next to it, which this directive does
 * not replace: `<select aglSelect id="role">`. Width and spacing belong to whoever places it.
 */
@Directive({
  selector: 'select[aglSelect]',
  host: {
    class:
      'block min-h-11 rounded-md border border-border bg-surface px-3 py-2 text-sm ' +
      'text-foreground shadow-sm focus-visible:outline-2 focus-visible:outline-offset-1 ' +
      'focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-60 ' +
      'aria-invalid:border-danger',
  },
})
export class Select {}
