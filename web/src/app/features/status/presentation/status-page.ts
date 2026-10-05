import { Component, inject } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

import { StatusFacade } from '../application/status.facade';

/** Environment status: proves that the web application talks to the API. */
@Component({
  selector: 'agl-status-page',
  imports: [TranslocoDirective],
  providers: [StatusFacade],
  templateUrl: './status-page.html',
  styleUrl: './status-page.scss',
})
export class StatusPage {
  private readonly facade = inject(StatusFacade);

  protected readonly serviceStatus = this.facade.serviceStatus;
  protected readonly checking = this.facade.checking;
  protected readonly failed = this.facade.failed;

  protected refresh(): void {
    this.facade.refresh();
  }
}
