import { Component, inject } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';

import { StatusFacade } from '../application/status.facade';

/** Environment status: proves that the web application talks to the API. */
@Component({
  selector: 'agl-status-page',
  imports: [TranslocoDirective, Button],
  providers: [StatusFacade],
  templateUrl: './status-page.html',
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
