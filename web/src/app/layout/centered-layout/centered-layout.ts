import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

/**
 * Frame of the screens before entering a team (the team selector and its form): the
 * brand centered above a single card, without the application header. It follows the
 * mockups of those screens.
 */
@Component({
  selector: 'agl-centered-layout',
  imports: [RouterOutlet, TranslocoDirective],
  templateUrl: './centered-layout.html',
})
export class CenteredLayout {
  /** The product name is a brand: it is not translated. */
  protected readonly brand = 'Agilina';
}
