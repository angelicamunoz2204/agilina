import { Component } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

/** Top bar of every screen: the brand and what Agilina is. */
@Component({
  selector: 'agl-header',
  imports: [TranslocoDirective],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header {
  /** The product name is a brand: it is not translated. */
  protected readonly brand = 'Agilina';
}
