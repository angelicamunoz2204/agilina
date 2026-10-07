import { Component } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

/**
 * The page for an address that names no organization (AD-29): `/`, a misspelled tenant, one
 * that does not exist or is suspended. The API gives the same answer for all of them, and so
 * does this page: it never says which one it was.
 */
@Component({
  selector: 'agl-not-found-page',
  imports: [TranslocoDirective],
  templateUrl: './not-found-page.html',
})
export class NotFoundPage {}
