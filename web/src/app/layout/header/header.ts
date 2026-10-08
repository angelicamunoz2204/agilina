import { Component, computed, inject } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

import { ShellContext } from '@core/shell/shell-context';

/**
 * Top bar of every screen: the brand and, inside a team, the team's name and the label of
 * the label of the user's role in it, and on the right the user's name. Outside a team it says
 * what Agilina is.
 */
@Component({
  selector: 'agl-header',
  imports: [TranslocoDirective],
  templateUrl: './header.html',
})
export class Header {
  /** The product name is a brand: it is not translated. */
  protected readonly brand = 'Agilina';
  protected readonly team = inject(ShellContext).team;
  /** The first letters of the first two words of the name, in capitals. */
  protected readonly initials = computed(() =>
    (this.team()?.userName ?? '')
      .split(/\s+/)
      .filter((word) => word.length > 0)
      .slice(0, 2)
      .map((word) => word.charAt(0).toUpperCase())
      .join(''),
  );
}
