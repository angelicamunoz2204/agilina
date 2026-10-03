import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { I18nService } from '../../../core/i18n/i18n.service';
import { StatusFacade } from '../application/status.facade';

@Component({
  selector: 'agl-status-page',
  imports: [],
  templateUrl: './status-page.html',
  styleUrl: './status-page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatusPage {
  private readonly facade = inject(StatusFacade);
  private readonly i18n = inject(I18nService);

  protected readonly status = this.facade.status;
  protected readonly checking = this.facade.checking;
  protected readonly failed = this.facade.failed;
  protected readonly t = this.i18n.t.bind(this.i18n);

  constructor() {
    this.refresh();
  }

  protected refresh(): void {
    this.facade.refresh();
  }
}
